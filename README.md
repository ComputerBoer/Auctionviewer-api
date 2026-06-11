# PythonAuctionviewer

## Run dev server
To run the development server run `python app.py` in the root of the project

## Update dependencies on webserver....
In august 2025 i just did a full reconfigure of the application, it just didnt work
  - removed domain + python application
  - readded domain + correct folder < use unique foldername to not have errors
    - create python app in empty folder
    - folder in python settings for startup is `domains/{{foldername}}` 
    - copy files into folder
    <!-- - restart application -->
    - add `requirements.txt` to configuration files
    - save application
    - run `pip install requirements.txt` via button
    - restart application
  