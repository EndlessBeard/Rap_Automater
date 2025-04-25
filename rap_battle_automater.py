#!/usr/bin/env python3
"""
Rap Battle Automater - A tool to generate rap battles using Gemini API
"""

import os
import json
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv('GEMINI_API_KEY.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Define directories
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAS_DIR = os.path.join(CURRENT_DIR, 'RapBattles', 'Personas')
MUSIC_DIR = os.path.join(CURRENT_DIR, 'RapBattles', 'Music')
FORMATS_DIR = os.path.join(CURRENT_DIR, 'RapBattles', 'Formats')
KNOWLEDGE_DIR = os.path.join(CURRENT_DIR, 'RapBattles', 'Knowledge')
OUTPUT_DIR = os.path.join(CURRENT_DIR, 'RapBattles', 'Rap Battles')

# Define file paths for fixed resources
RHYME_SCHEMES_PATH = os.path.join(KNOWLEDGE_DIR, 'Rhyme Schemes.md')
COMPETITION_FORMAT_PATH = os.path.join(KNOWLEDGE_DIR, 'Rap_Battle_Competition_Format.md')
INTRO_A_PATH = os.path.join(CURRENT_DIR, 'RapBattles', 'Rap Battle Intro A.md')
INTRO_B_PATH = os.path.join(CURRENT_DIR, 'RapBattles', 'Rap Battle Intro B.md')

# Define Gemini Model names - Using only PRIMARY_MODEL for consistency
PRIMARY_MODEL = "models/gemini-2.5-flash-preview-04-17"

# Utility Functions for File Operations
def get_files_in_directory(directory, extension='.json'):
    """Get all files of a specific type in a directory."""
    files = []
    if os.path.exists(directory):
        for file in os.listdir(directory):
            if file.endswith(extension):
                files.append(file)
    return files

def get_simplified_filename(filename):
    """Remove extension from filename."""
    return os.path.splitext(filename)[0]

def load_json_file(filepath):
    """Load and parse JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return None

def load_md_file(filepath):
    """Load markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading markdown file {filepath}: {e}")
        return None

def extract_stage_name(persona_json):
    """Extract stage name from persona JSON."""
    try:
        return persona_json.get('stage_name', '')
    except Exception:
        return ''

def parse_music_sections(music_json):
    """Parse music JSON into required sections."""
    sections = []
    
    # First section: All metadata excluding sections array
    metadata = {k: v for k, v in music_json[0].items() if k != 'sections'}
    sections.append(json.dumps(metadata, indent=2))
    
    # Add the 6 sections from the music file
    music_sections = music_json[0].get('sections', [])
    for section in music_sections:
        sections.append(json.dumps(section, indent=2))
    
    return sections

def create_intro_copy(intro_template, persona_data):
    """Create personalized intro from template."""
    intro_text = intro_template
    
    # Replace placeholders with persona data
    if 'stage_name' in persona_data:
        intro_text = intro_text.replace('[OPPONENT_NICKNAME]', persona_data['stage_name'])
    
    if 'first_name' in persona_data:
        intro_text = intro_text.replace('[OPPONENT_NAME]', persona_data['first_name'])
    
    if 'last_name' in persona_data:
        intro_text = intro_text.replace('[OPPONENT_LASTNAME]', persona_data['last_name'])
    
    return intro_text

def prepare_context_for_api(files_dict):
    """Format context with clear headers for Gemini API."""
    context = ""
    
    for label, content in files_dict.items():
        if content:
            if label.endswith('.json'):
                context += f"### {label} (JSON):\n{content}\n\n"
            elif label.endswith('.md'):
                context += f"### {label} (MARKDOWN):\n{content}\n\n"
            else:
                context += f"### {label}:\n{content}\n\n"
    
    return context

def save_output_to_file(filename, content):
    """Save content to a file in the output directory."""
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        return True, filepath
    except Exception as e:
        return False, str(e)

# Gemini API Functions
def initialize_api_client():
    """Set up Gemini API client with key validation."""
    genai.configure(api_key=GEMINI_API_KEY)
    return genai

def validate_api_key():
    """Validate Gemini API key with a simple test query."""
    try:
        client = initialize_api_client()
        model = client.GenerativeModel(PRIMARY_MODEL)
        response = model.generate_content("Test connection.")
        return True, "API key validated successfully."
    except Exception as e:
        return False, f"API key validation failed: {str(e)}"

def handle_rate_limit(retry_count):
    """Calculate and implement pause for rate limiting using a more conservative approach."""
    # Start with longer initial pause and increase more aggressively
    # Initial pause of 5 seconds, then 10, 20, 40, 80, etc.
    pause_time = 5 * (2 ** retry_count)
    # Cap the maximum wait time at 2 minutes
    pause_time = min(pause_time, 120)
    time.sleep(pause_time)
    return pause_time

def send_to_gemini(context, retry_count=0, max_retries=7):
    """Send content to Gemini API with improved rate limit handling."""
    client = initialize_api_client()
    model_name = PRIMARY_MODEL
    
    try:
        model = client.GenerativeModel(model_name)
        response = model.generate_content(context)
        return True, response.text
    except Exception as e:
        error_message = str(e)
        
        # Check if it's a rate limit issue
        if "quota" in error_message.lower() or "rate" in error_message.lower():
            if retry_count < max_retries:
                pause_time = handle_rate_limit(retry_count)
                print(f"Rate limit encountered. Pausing for {pause_time} seconds before retry {retry_count + 1}/{max_retries}")
                return send_to_gemini(context, retry_count + 1, max_retries)
            else:
                return False, f"Rate limit exceeded after {max_retries} retries. Please try again later."
        
        return False, f"API Error: {error_message}"

def combine_battle_sections(sections_dict):
    """Combine battle sections into final markdown output."""
    combined = "# Rap Battle\n\n"
    
    # Add rapper info if available with full names including first name, nickname, and last name
    if all(key in sections_dict for key in ['rapper_a_name', 'rapper_b_name']):
        # Get first and last names if available
        rapper_a_first = sections_dict.get('rapper_a_first', '')
        rapper_a_last = sections_dict.get('rapper_a_last', '')
        rapper_b_first = sections_dict.get('rapper_b_first', '')
        rapper_b_last = sections_dict.get('rapper_b_last', '')
        
        # Format rapper A's full name
        rapper_a_full = ""
        if rapper_a_first:
            rapper_a_full += f"{rapper_a_first} "
        if sections_dict['rapper_a_name']:
            rapper_a_full += f"\"{sections_dict['rapper_a_name']}\" "
        if rapper_a_last:
            rapper_a_full += rapper_a_last
        rapper_a_full = rapper_a_full.strip()
        
        # Format rapper B's full name
        rapper_b_full = ""
        if rapper_b_first:
            rapper_b_full += f"{rapper_b_first} "
        if sections_dict['rapper_b_name']:
            rapper_b_full += f"\"{sections_dict['rapper_b_name']}\" "
        if rapper_b_last:
            rapper_b_full += rapper_b_last
        rapper_b_full = rapper_b_full.strip()
        
        # Use stage name if full name is empty
        if not rapper_a_full.strip():
            rapper_a_full = sections_dict['rapper_a_name']
        if not rapper_b_full.strip():
            rapper_b_full = sections_dict['rapper_b_name']
            
        combined += f"## {rapper_a_full} vs {rapper_b_full}\n\n"
    
    # Add music info if available
    if 'music_title' in sections_dict:
        combined += f"*Music: {sections_dict['music_title']}*\n\n"
    
    # Add all battle sections
    for i in range(1, 7):  # 6 sections
        section_key = f'section_{i}'
        if section_key in sections_dict:
            # Add section header
            if i % 2 == 1:  # Odd sections are Rapper A
                combined += f"### Rapper A - Verse {(i + 1) // 2}\n\n"
            else:  # Even sections are Rapper B
                combined += f"### Rapper B - Verse {i // 2}\n\n"
            
            combined += f"{sections_dict[section_key]}\n\n"
    
    return combined

# Main Application Class
class RapBattleAutomater:
    def __init__(self, root):
        self.root = root
        self.root.title("Rap Battle Automater")
        self.root.geometry("800x600")
        
        # Set app icon if available
        # self.root.iconbitmap('path/to/icon.ico')  # Uncomment and add path if you have an icon
        
        # Variables
        self.persona_a_var = tk.StringVar()
        self.persona_b_var = tk.StringVar()
        self.music_var = tk.StringVar()
        self.output_filename_var = tk.StringVar()
        
        # Create UI elements
        self.create_ui()
        
        # Populate dropdowns
        self.populate_dropdowns()
        
        # States for battle generation
        self.battle_sections = {}
        self.is_generating = False
    
    def create_ui(self):
        """Create all UI elements."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Selection area
        selection_frame = ttk.LabelFrame(main_frame, text="Battle Configuration", padding="10")
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Persona A selection
        ttk.Label(selection_frame, text="Persona A:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        persona_a_combobox = ttk.Combobox(selection_frame, textvariable=self.persona_a_var, state="readonly", width=30)
        persona_a_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        persona_a_combobox.bind("<<ComboboxSelected>>", self.update_output_filename)
        
        # Persona B selection
        ttk.Label(selection_frame, text="Persona B:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        persona_b_combobox = ttk.Combobox(selection_frame, textvariable=self.persona_b_var, state="readonly", width=30)
        persona_b_combobox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        persona_b_combobox.bind("<<ComboboxSelected>>", self.update_output_filename)
        
        # Music selection
        ttk.Label(selection_frame, text="Music:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        music_combobox = ttk.Combobox(selection_frame, textvariable=self.music_var, state="readonly", width=30)
        music_combobox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Output filename
        ttk.Label(selection_frame, text="Output Filename:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        output_entry = ttk.Entry(selection_frame, textvariable=self.output_filename_var, width=30)
        output_entry.grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Battle button
        battle_button = ttk.Button(selection_frame, text="Rap Battle!!", command=self.start_battle)
        battle_button.grid(row=4, column=0, columnspan=2, padx=5, pady=10)
        
        # Log display area
        log_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrolled text widget for log
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def populate_dropdowns(self):
        """Populate all dropdown menus."""
        # Get persona files
        persona_files = get_files_in_directory(PERSONAS_DIR, '.json')
        persona_names = [get_simplified_filename(f) for f in persona_files]
        
        # Get music files
        music_files = get_files_in_directory(MUSIC_DIR, '.json')
        music_names = [get_simplified_filename(f) for f in music_files]
        
        # Update comboboxes
        persona_a_combobox = self.root.nametowidget(self.root.winfo_children()[0].winfo_children()[0].winfo_children()[1])
        persona_a_combobox['values'] = persona_names
        
        persona_b_combobox = self.root.nametowidget(self.root.winfo_children()[0].winfo_children()[0].winfo_children()[3])
        persona_b_combobox['values'] = persona_names
        
        music_combobox = self.root.nametowidget(self.root.winfo_children()[0].winfo_children()[0].winfo_children()[5])
        music_combobox['values'] = music_names
    
    def update_output_filename(self, event=None):
        """Update output filename based on selected personas."""
        persona_a = self.persona_a_var.get()
        persona_b = self.persona_b_var.get()
        
        if persona_a and persona_b:
            self.output_filename_var.set(f"{persona_a}_vs_{persona_b}.md")
    
    def log_message(self, message):
        """Add message to log display."""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        self.root.update_idletasks()
    
    def update_status(self, message):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def start_battle(self):
        """Start the rap battle generation process in a separate thread."""
        # Validate selections
        if not self.persona_a_var.get():
            messagebox.showerror("Error", "Please select Persona A")
            return
        
        if not self.persona_b_var.get():
            messagebox.showerror("Error", "Please select Persona B")
            return
        
        if not self.music_var.get():
            messagebox.showerror("Error", "Please select Music")
            return
        
        if not self.output_filename_var.get():
            messagebox.showerror("Error", "Please enter an output filename")
            return
        
        # Add .md extension if not present
        if not self.output_filename_var.get().endswith('.md'):
            self.output_filename_var.set(self.output_filename_var.get() + '.md')
        
        # Prevent multiple generation processes
        if self.is_generating:
            messagebox.showinfo("Info", "Battle generation is already in progress")
            return
        
        # Start generation in a separate thread to keep UI responsive
        self.is_generating = True
        threading.Thread(target=self.generate_battle).start()
    
    def generate_battle(self):
        """Generate the complete rap battle."""
        try:
            self.log_message("Starting battle generation process...")
            self.update_status("Generating battle...")
            
            # Step 1: Validate API Key
            self.log_message("Validating API key...")
            valid, message = validate_api_key()
            self.log_message(message)
            
            if not valid:
                messagebox.showerror("API Error", "Could not validate API key. Please check your API key and try again.")
                self.is_generating = False
                self.update_status("Failed: API key invalid")
                return
            
            # Step 2: Load Files
            self.log_message("Loading selected files...")
            
            # Load persona files
            persona_a_path = os.path.join(PERSONAS_DIR, f"{self.persona_a_var.get()}.json")
            persona_b_path = os.path.join(PERSONAS_DIR, f"{self.persona_b_var.get()}.json")
            
            persona_a_data = load_json_file(persona_a_path)
            persona_b_data = load_json_file(persona_b_path)
            
            if not persona_a_data or not persona_b_data:
                messagebox.showerror("Error", "Failed to load persona files")
                self.is_generating = False
                self.update_status("Failed: Persona file error")
                return
            
            # Extract persona names for the final output
            self.battle_sections['rapper_a_name'] = extract_stage_name(persona_a_data)
            self.battle_sections['rapper_b_name'] = extract_stage_name(persona_b_data)
            
            # Extract first and last names for the full name format
            self.battle_sections['rapper_a_first'] = persona_a_data.get('first_name', '')
            self.battle_sections['rapper_a_last'] = persona_a_data.get('last_name', '')
            self.battle_sections['rapper_b_first'] = persona_b_data.get('first_name', '')
            self.battle_sections['rapper_b_last'] = persona_b_data.get('last_name', '')
            
            # Load music file
            music_path = os.path.join(MUSIC_DIR, f"{self.music_var.get()}.json")
            music_data = load_json_file(music_path)
            
            if not music_data:
                messagebox.showerror("Error", "Failed to load music file")
                self.is_generating = False
                self.update_status("Failed: Music file error")
                return
            
            # Store music title for final output
            self.battle_sections['music_title'] = music_data[0].get('title', self.music_var.get())
            
            # Parse music into sections
            music_sections = parse_music_sections(music_data)
            
            # Load fixed resources
            rhyme_schemes = load_md_file(RHYME_SCHEMES_PATH)
            competition_format = load_md_file(COMPETITION_FORMAT_PATH)
            intro_a_template = load_md_file(INTRO_A_PATH)
            intro_b_template = load_md_file(INTRO_B_PATH)
            
            if not all([rhyme_schemes, competition_format, intro_a_template, intro_b_template]):
                messagebox.showerror("Error", "Failed to load required resources")
                self.is_generating = False
                self.update_status("Failed: Resource loading error")
                return
            
            # Create personalized intros
            intro_a = create_intro_copy(intro_a_template, persona_a_data)
            intro_b = create_intro_copy(intro_b_template, persona_b_data)
            
            # Step 3: Session A - First Rapper
            self.log_message("Generating first verse from Rapper A...")
            
            session_a_context = prepare_context_for_api({
                'Persona.json': json.dumps(persona_a_data, indent=2),
                'Music.json': music_sections[0],  # General music metadata
                'Competition_Format.md': competition_format,
                'Rhyme_Schemes.md': rhyme_schemes,
                'Intro.md': intro_a,
                'Music_Section.json': music_sections[1]  # First section
            })
            
            # Send to Gemini API with improved rate limit handling
            success, response_text = send_to_gemini(session_a_context)
            
            if not success:
                messagebox.showerror("API Error", response_text)
                self.is_generating = False
                self.update_status("Failed: API error")
                return
            
            # Store first verse
            session_a_section_1 = response_text
            self.battle_sections['section_1'] = session_a_section_1
            self.log_message("First verse generated successfully!")
            
            # Add a short pause between API calls to avoid hitting rate limits
            self.log_message("Pausing briefly before next API call...")
            time.sleep(2)
            
            # Step 4: Session B - Second Rapper (First Response)
            self.log_message("Generating first verse from Rapper B...")
            
            session_b_context = prepare_context_for_api({
                'Persona.json': json.dumps(persona_b_data, indent=2),
                'Music.json': music_sections[0],  # General music metadata
                'Competition_Format.md': competition_format,
                'Rhyme_Schemes.md': rhyme_schemes,
                'Intro.md': intro_b,
                'Music_Section.json': music_sections[2],  # Second section
                'Opponent_Verse.md': session_a_section_1
            })
            
            # Send to Gemini API
            success, response_text = send_to_gemini(session_b_context)
            
            if not success:
                messagebox.showerror("API Error", response_text)
                self.is_generating = False
                self.update_status("Failed: API error")
                return
            
            # Store second verse
            session_b_section_2 = response_text
            self.battle_sections['section_2'] = session_b_section_2
            self.log_message("Second verse generated successfully!")
            
            # Add a short pause between API calls to avoid hitting rate limits
            self.log_message("Pausing briefly before next API call...")
            time.sleep(2)
            
            # Step 5: Continue alternating sessions for remaining verses
            # Session A - Second Verse
            self.log_message("Generating second verse from Rapper A...")
            
            session_a_context = prepare_context_for_api({
                'Persona.json': json.dumps(persona_a_data, indent=2),
                'Music.json': music_sections[0],  # General music metadata
                'Competition_Format.md': competition_format,
                'Rhyme_Schemes.md': rhyme_schemes,
                'Music_Section.json': music_sections[3],  # Third section
                'Previous_Verse.md': session_a_section_1,
                'Opponent_Response.md': session_b_section_2
            })
            
            # Send to Gemini API
            success, response_text = send_to_gemini(session_a_context)
            
            if not success:
                messagebox.showerror("API Error", response_text)
                self.is_generating = False
                self.update_status("Failed: API error")
                return
            
            # Store third verse
            session_a_section_3 = response_text
            self.battle_sections['section_3'] = session_a_section_3
            self.log_message("Third verse generated successfully!")
            
            # Add a short pause between API calls to avoid hitting rate limits
            self.log_message("Pausing briefly before next API call...")
            time.sleep(2)
            
            # Session B - Second Verse
            self.log_message("Generating second verse from Rapper B...")
            
            session_b_context = prepare_context_for_api({
                'Persona.json': json.dumps(persona_b_data, indent=2),
                'Music.json': music_sections[0],  # General music metadata
                'Competition_Format.md': competition_format,
                'Rhyme_Schemes.md': rhyme_schemes,
                'Music_Section.json': music_sections[4],  # Fourth section
                'Previous_Verse.md': session_b_section_2,
                'Opponent_Response.md': session_a_section_3
            })
            
            # Send to Gemini API
            success, response_text = send_to_gemini(session_b_context)
            
            if not success:
                messagebox.showerror("API Error", response_text)
                self.is_generating = False
                self.update_status("Failed: API error")
                return
            
            # Store fourth verse
            session_b_section_4 = response_text
            self.battle_sections['section_4'] = session_b_section_4
            self.log_message("Fourth verse generated successfully!")
            
            # Add a short pause between API calls to avoid hitting rate limits
            self.log_message("Pausing briefly before next API call...")
            time.sleep(2)
            
            # Session A - Final Verse
            self.log_message("Generating final verse from Rapper A...")
            
            session_a_context = prepare_context_for_api({
                'Persona.json': json.dumps(persona_a_data, indent=2),
                'Music.json': music_sections[0],  # General music metadata
                'Competition_Format.md': competition_format,
                'Rhyme_Schemes.md': rhyme_schemes,
                'Music_Section.json': music_sections[5],  # Fifth section
                'Previous_Verses.md': f"{session_a_section_1}\n\n{session_a_section_3}",
                'Opponent_Responses.md': f"{session_b_section_2}\n\n{session_b_section_4}"
            })
            
            # Send to Gemini API
            success, response_text = send_to_gemini(session_a_context)
            
            if not success:
                messagebox.showerror("API Error", response_text)
                self.is_generating = False
                self.update_status("Failed: API error")
                return
            
            # Store fifth verse
            session_a_section_5 = response_text
            self.battle_sections['section_5'] = session_a_section_5
            self.log_message("Fifth verse generated successfully!")
            
            # Add a short pause between API calls to avoid hitting rate limits
            self.log_message("Pausing briefly before next API call...")
            time.sleep(2)
            
            # Session B - Final Verse
            self.log_message("Generating final verse from Rapper B...")
            
            session_b_context = prepare_context_for_api({
                'Persona.json': json.dumps(persona_b_data, indent=2),
                'Music.json': music_sections[0],  # General music metadata
                'Competition_Format.md': competition_format,
                'Rhyme_Schemes.md': rhyme_schemes,
                'Music_Section.json': music_sections[6],  # Sixth section
                'Previous_Verses.md': f"{session_b_section_2}\n\n{session_b_section_4}",
                'Opponent_Responses.md': f"{session_a_section_1}\n\n{session_a_section_3}\n\n{session_a_section_5}"
            })
            
            # Send to Gemini API
            success, response_text = send_to_gemini(session_b_context)
            
            if not success:
                messagebox.showerror("API Error", response_text)
                self.is_generating = False
                self.update_status("Failed: API error")
                return
            
            # Store sixth verse
            session_b_section_6 = response_text
            self.battle_sections['section_6'] = session_b_section_6
            self.log_message("Sixth verse generated successfully!")
            
            # Step 6: Combine all sections into final output
            self.log_message("Combining all verses into final output...")
            final_output = combine_battle_sections(self.battle_sections)
            
            # Step 7: Save to file
            self.log_message("Saving battle to file...")
            success, result = save_output_to_file(self.output_filename_var.get(), final_output)
            
            if success:
                self.log_message(f"Rap battle saved successfully to: {result}")
                messagebox.showinfo("Success", f"Rap battle generated and saved to:\n{result}")
                self.update_status("Complete: Battle saved")
            else:
                messagebox.showerror("Error", f"Failed to save output: {result}")
                self.update_status("Failed: Could not save output")
        
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self.update_status("Failed: Unexpected error")
        
        finally:
            self.is_generating = False

# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = RapBattleAutomater(root)
    root.mainloop()