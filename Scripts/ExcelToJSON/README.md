# Excel to JSON

## Introduction

This Python script was developed to convert an Excel worksheet full of threat 
intelligence indicators to JSON format.  We can then import the JSON list 
to Azure Sentinel using a Logic App.

## Before You Start

1. Install Python 3
1. Install PIP

## Getting Started

1. Create a virtual environment in a folder named "env"  
   ```python -m venv env```
1. Activate the virtual environment  
   ```.\env\Scripts\activate```
1. Install the packages from "requirements.txt"  
   ```pip install -r requirements.txt```
1. Run the code  
   ```excel_to_json.py <options>```  
   -OR-  
   ```python excel_to_json.py <options>```
1. Use "--help" to display the help options  
   ```excel_to_json.py --help```  
   -OR-  
   ```python excel_to_json.py --help```
