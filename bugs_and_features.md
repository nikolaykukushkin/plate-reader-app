CURRENT BEHAVIOR
app accepts txt files, but does not accept xls files from the plate reader. The xls files might be non-standard because Excel gives warning when opening them (this is the plate reader's fault). Saving the xls as txt solves the problem, but is complicated. Standard use case is 20260212_MF_dilution_NK.xls
EXPECTED BEHAVIOR
app accepts the xls as is from the plate reader.
FIXED? [x]


CURRENT BEHAVIOR
Parsing is not flexible enough. Only one experiment per spreadsheet is allowed. There is a "manual selection" button that does not work.
EXPECTED BEHAVIOR
-Full spreadsheet is displayed in a field upon import, and users can select relevant areas of data by selecting them. Users can select areas related to different experiments which can be added using a separate button, and named with dates and initials. Number of samples auto-populates depending on selection. There should be a way to add multiple selections to one experiment, for example if the number of samples of 15 it would need to be selected as a 2x6 area and then a separate 1x3 area.
-When experiments are created during parsing, their names, dates, and experimenter initials should be autopopulated from file names but editable. The typical format of a file name is YYYYMMDD_expname_operatorinit.xls. If there are multiple experiments, the name could be YYYYMMDD_expname1_operatorinit_YYYYMMDD_expname2_operatorinit.xls etc. There should be an option to add a letter to the date if two experiments are done on the same day, for example 20260205A and 20260205B.
-Selecting luciferase data then creates an option to select relevant data areas in the Bradford part of the spreadsheet. (There is never Bradford without luciferase). Not all luciferase samples will have associated Bradford data, so the Bradford cannot be mandatory but available if experiments are created from luciferase data. 
-After selecting the Bradford samples/standards areas, the interface calculates the number of technical replicates for Bradford standard and samples. The replicates of Bradford standards are calculated from the number of columns in the selected Bradford area, since Bradford standards always run top to bottom, so however wide the selection is is how many replicates there are in each line. The number of replicates among Bradford samples, however, can be different, for example a 6 column, 8-row dataset could be 16 samples with 3 replicates each, or 24 samples with 2 replicates each. The number of replicates should be calculated by comparing the selected Bradford area to the number of luciferase samples added to the corresponding experiment. So, if 24 luciferase samples are added and 48 bradford cells selected, this means that the number of bradford sample replicates is 2. If an even number cannot be calculated, return an "uneven number" error
-The system must allow for some samples that are standardized to Bradford and some that are not. These can occur within the same spreadsheet. A difficult use case is in plate-reader-app/20260205A_reverse transpant_20260206B_MF_dilns_20260129_fixed_transfer.xls. In this document, there are three experiments in a single spreadsheet: 1-16 are 20260205A (not standardized to Bradford), 20260206B (standardized to Bradford - the only Bradford samples in the spreadsheet), and 20260129 (not standardized to bradford). The system should detect in which experiments there are Bradford data present, and automatically standardize them to such, but allow the user an option to uncheck this for specific samples.
-Manual selection button is removed because it is no longer needed.
FIXED? []

CURRENT BEHAVIOR
Users need to input sample names one by one by clicking on each field
EXPECTED BEHAVIOR
Users should be able to copy and paste a column of cells from an excel spreadsheet, or advance from cell to cell by hitting enter while typing.
FIXED? []

CURRENT BEHAVIOR
Standards/standard concentration input forms are displayed wrong, they show up diagonally
EXPECTED BEHAVIOR
The standards are stacked one upon another. As with cell names, users can copy and paste an entire column of numbers.
FIXED? []

CURRENT BEHAVIOR
App looks clunky and "sciency"
EXPECTED BEHAVIOR
App looks pretty and sleek, inviting to use, while still scientific.
FIXED? []

