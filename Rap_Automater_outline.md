- Build a Rap Battle Automater
*   **Goal:** Create a python App that Automatically produces rap battles using two different Gemini sessions simuetanously.
*   **Intented Function and Flow**
    1)  User selects two personas(labeled, Persona_A, and Persona_B) from a drop down menu populated automaticaly by referencing a directory named, Personas
    2)  User selects music from a drop down menu populated automatically by referencing a directory named, Music
    3)  User clicks a button labeled, Rap Battle!!
    4)  The Script parses the Music file into 7 sections 
        *   The first section is for all non-outline text blocks.
        *   Sections 2-7 are for each section of the outlined music.
            *   Sections are labeled as Music_Section_[1-6], ex. Music_Section_2
    5)  The Script prepares the intros
        *   Parses both Personas for the Stage Name.
        *   Creates a temporary copy of each intro with the Stage_Name replaced by the releveant Persona
    6)  The script opens Session A
        *   Uploads: Persona_A, Music, Rap_Battle_Competition_Format, Rhyme Schemes, Intro_A Copy, Music_Section_1
        *   Receives a structured response, labeled Session_A_Section_1
    7)  The script opens Session B
        *   Uploads: Persona_A, Music, Rap_Battle_Competition_Format, Rhyme Schemes, Intro_B Copy, Music_Section_2, Session_A_Section_1
        *   Recieves a structured response, labeled Session_B_Section_2
    8)  Session_B_Section_2 and Music_Section_3 is sent to Session_A
        *   Recieves a structured response, labeled Session_A_Section_3
    9)  Session_A_Section_3 and Music_Section_4 is sent to Session_B
        *   Recieves a structured response, labeled Session_B_Section_4
    10) Session_B_Section_4 and Music_Section_5 is sent to Session_A
        *   Recieves a structured response, labeled Session_A_Section_5
    11) Session_A_Section_5 and Music_Section_6 is sent to Session_B
        *   Recieves a structured response, labeled Session_B_Section_6
    12) The six resulting responses are joined togeather in to a consise readable format and saved into a directory named Rap Battles, in .md format
*   **UI**
    *   Persona A and B Drop, Down Menus
    *   Music, Drop Down Menu
    *   Output Filename, text box
    *   Output Display for error logging, processing related messages. This should be an actively updated element
*   **Token Limit Monitor**
    *   Token Limit Monitoring should be employed to avoid errors

