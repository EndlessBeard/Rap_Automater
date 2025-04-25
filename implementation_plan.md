# Rap Battle Automater - Implementation Plan

## Overview
This Python application automatically generates rap battles using the Gemini API. It creates battles between two rapper personas over specified music tracks, handling the back-and-forth exchange using two independent Gemini API contexts.

## File Structure Requirements
- Use JSON format for all Persona and Music files
- Use Markdown for format rules, rhyme schemes, and intro files
- When sending to Gemini API, clearly label each file type with headers

## UI Components (Tkinter)
1. **Dropdown Menus**
   - Persona A dropdown (populated from Personas directory, JSON files only)
   - Persona B dropdown (populated from Personas directory, JSON files only)
   - Music dropdown (populated from Music directory, JSON files only)
   - All dropdowns should show simplified names without file extensions

2. **Text Fields**
   - Output filename field (auto-populated with "[PersonaA]_vs_[PersonaB].md" when both personas selected)
   
3. **Buttons**
   - "Rap Battle!!" button to start the generation process
   
4. **Display Area**
   - Text area for logging progress, errors, and status updates

## Processing Steps

1. **File Loading and Parsing**
   - Load and parse selected persona JSON files
   - Load and parse selected music JSON file
   - Parse Music file into 7 sections:
     - First section: All non-outline metadata (title, genre, etc.)
     - Sections 2-7: The 6 outlined music sections

2. **Intro Preparation**
   - Extract Stage Name from both persona files
   - Create temporary copies of intro files with placeholders replaced

3. **API Interaction Flow**
   - **Session A (First Rapper)**
     - Upload: Persona A, Music, Rap Battle Competition Format, Rhyme Schemes, Intro A, Music Section 1
     - Receive response: Session_A_Section_1
   
   - **Session B (Second Rapper)**
     - Upload: Persona B, Music, Rap Battle Competition Format, Rhyme Schemes, Intro B, Music Section 2, Session_A_Section_1
     - Receive response: Session_B_Section_2
   
   - **Alternating Sessions**
     - Send Session_B_Section_2 and Music_Section_3 to Session A
     - Send Session_A_Section_3 and Music_Section_4 to Session B
     - Send Session_B_Section_4 and Music_Section_5 to Session A
     - Send Session_A_Section_5 and Music_Section_6 to Session B
   
   - **Final Output**
     - Combine all six sections into a single markdown file
     - Save to Rap Battles directory with the specified filename

## API Implementation

1. **API Client**
   - Create a single Gemini API client
   - Manage session contexts independently for each rapper
   
2. **API Key and Model Selection**
   - Use GEMINI_API_KEY.env for API key
   - Primary model: gemini-2.5-flash-preview-0501
   - Fallback model: gemini-2.5-flash-preview-0417
   
3. **Error Handling**
   - Validate API key on first use
   - Implement fallback to alternative model if primary fails
   - Use pauses with increasing duration to handle rate limits
   - Log all errors and API responses to the UI display

## Utility Functions

1. **File Operations**
   - `load_json_file(filepath)` - Load and parse JSON files
   - `load_md_file(filepath)` - Load markdown files
   - `get_files_in_directory(directory, extension)` - Get all files of a specific type in a directory
   - `extract_stage_name(persona_json)` - Extract stage name from persona JSON

2. **Formatting Functions**
   - `create_intro_copy(intro_template, persona)` - Create a personalized intro from template
   - `parse_music_sections(music_json)` - Split music file into required sections
   - `prepare_context_for_api(files_dict)` - Format context for Gemini API with clear headers
   - `combine_battle_sections(sections_dict)` - Combine battle sections into final output

3. **API Interaction**
   - `initialize_api_client()` - Set up Gemini API client with key validation
   - `send_to_gemini(session_context, content)` - Send content to Gemini API and handle responses
   - `handle_rate_limit(retry_count)` - Calculate and implement pauses for rate limiting

## Implementation Notes
- Use a single Gemini client with separate session contexts for each rapper
- Keep file formats separate with clear headers when sending to API
- Show only .json files in dropdowns with simplified names
- Implement progressive backoff for rate limit handling