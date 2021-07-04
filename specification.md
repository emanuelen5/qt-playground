# Specification
Specification for a time reporting tool:

# Views
* **Overview** <br>
  An overview over the current week. Perhaps also month (user preference).
* **Project list** <br>
  A list over projects, and view where new can be added.
* **Task bar** <br>
  Add a task bar icon for easy access when none of the windows are open. Add common tasks to it, like adding time to project and opening the other windows.
* **Report view** <br>
  A specific view for reporting. Might have to be adapted to specific time reporting tools.

# Functions
## Basic functions
* Quick-report function
  * Auto-completion on project ID:s to make it faster to report
  * Adding delta-times to work on specific projects during a day (e.g. adding 1h to a specific project)
    * Percentage split between projects
* Specifying main project during day for automatic calculation of unspecified time
* Saving the report to file.
* Notes for each corresponding delta-time

## More advanced functions
* Specific reporting GUI:s adapted for different time reporting tools. Added as plugins.
* Automatic reporting using GUI automation (e.g. tesseract and pyautogui)
* Project report, where each 
* Saving the partially reported time so it can be adjusted later on.
