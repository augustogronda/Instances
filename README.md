# Instances
A little Python script to run multiple instances of Google Chrome with Selenium 

## Features
- Select the number of Chrome instances to open.
- Choose the ChromeDriver executable directly through the interface.
- Button to close all open instances from the interface.

## Requirements

1. **Python 3.8+**  
   Ensure you have Python installed. Download it from [python.org](https://www.python.org/downloads/).

2. **Google Chrome**  
   Make sure Google Chrome is installed on your system.  

3. **Compatible ChromeDriver**  
   ChromeDriver must match the version of your installed Chrome browser.  
   - To check your Chrome version:  
     Open Chrome, navigate to `Settings > About Chrome`, and note the version number.

   - Download the matching ChromeDriver from:  
     [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/)


## Installation

1. Clone this repository or download the files to your local machine:
   ```bash
   git clone https://github.com/augustogronda/Instances.git
   ```
2. Install the required dependencies:
   ```bash
   pip install selenium
   ```
3. Make sure the ChromeDriver executable is on your system. The script allows you to select it through the interface.

---

## Usage

1. Run the script:
   ```bash
   python instancesIU.py
   ```
2. Use the graphical interface to:
   - Enter the desired number of instances.
   - Input the URL to open.
   - Choose the ChromeDriver executable.

3. Click the **Run** button to launch the instances.

4. Use the **Close Opened Windows** button to close all Chrome windows opened by the script.

---

## Notes

- **Memory Usage**:  
  Each Chrome instance typically uses between **50 MB and 200 MB of RAM**, depending on the loaded website.

- **ChromeDriver Compatibility**:  
  If you encounter issues related to ChromeDriver, ensure that its version matches your Chrome browser version.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

### Example Screenshots

#### User Interface
Include a screenshot of the interface here, for example:
![User Interface](./images/Instancesimage.jpg
)
