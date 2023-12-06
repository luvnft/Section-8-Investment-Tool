global map_file_path, csv_file_path
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
                             QComboBox, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, 
                             QFormLayout, QCheckBox, QGroupBox, QHeaderView, QListView, QSizePolicy, QSpacerItem)
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDesktopWidget, QGroupBox, QHBoxLayout, QGridLayout
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtGui import QPalette, QColor, QFont
import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFontMetrics
import qdarkstyle
import pandas as pd
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QScrollArea
import webbrowser
from PyQt5.QtWidgets import QMessageBox

# application_path = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    base_path = sys._MEIPASS
else:
    # Running as standard Python script
    base_path = os.path.dirname(os.path.abspath(__file__))

map_file_path = os.path.join(base_path, 'map.html')
csv_file_path = os.path.join(base_path, 's8_investment.csv')
# map_file_path = os.path.join(application_path, 'map.html')
# csv_file_path = os.path.join(application_path, 's8_investment.csv')

class CustomTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return self.text() < other.text()

class CustomLabel(QLabel):
    textChanged = pyqtSignal(str)

    def setText(self, text):
        super().setText(text)
        self.textChanged.emit(text)

class S8App(QMainWindow):
    def __init__(self, df):
        super().__init__()
        self.df = df
        self.DEFAULT_ROW_HEIGHT = 30  # You can adjust this value based on your requirements
        self.initUI()

    def initUI(self):
        global map_file_path, csv_file_path
        self.setWindowTitle('Section 8 Investment Tool')  # Consider changing 'S8 App' to 'Section 8 Investment Tool' if you'd like the window title to match
        self.setGeometry(100, 100, 1400, 700)
        mainLayout = QVBoxLayout()

        # Add the title label here:
        titleLabel = QLabel("Section 8 Investment Tool")
        titleLabel.setObjectName("TitleLabel")  # Assign a unique object name to the titleLabel
        titleLabel.setAlignment(Qt.AlignCenter)  # Center align the title
        mainLayout.addWidget(titleLabel)

        # Set style sheet
        app.setStyle("Fusion")
        self.setStyleSheet("""
            QLabel {font: 12pt Arial;}
            QComboBox {font: 12pt Arial;}
            QTableWidget {font: 12pt Arial;}
            QLabel#TitleLabel {font: 46pt Arial; font-weight: bold; color: #001F3F;}  # Set font and color of titleLabel using its objectName
        """)

        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)



        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(centralWidget)
        self.setCentralWidget(scroll)

        # Set a minimum width for the main window
        self.setMinimumWidth(1000)  # Adjust this value as needed
        # Set a minimum height for the main window
        self.setMinimumHeight(1200)
        # Map section
        self.mapLayout = QVBoxLayout()
        # Initialize map with the USA view
        m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
        m.save(map_file_path)
        # Display map in a QWebEngineView
        self.mapView = QWebEngineView()
        MAP_WIDTH = 1200  # or whatever width you desire
        MAP_HEIGHT = 600  # or whatever height you desire
        self.mapView.setFixedWidth(MAP_WIDTH)
        self.mapView.setFixedHeight(MAP_HEIGHT)
        self.mapView.load(QUrl.fromLocalFile(map_file_path))

        self.mapLayout = QHBoxLayout()  # Assuming a horizontal layout; adjust if using QVBoxLayout
        self.mapLayout.addStretch(1)  # This adds a stretchable space before the map
        self.mapLayout.addWidget(self.mapView)  # This adds the map
        self.mapLayout.addStretch(1)  # This adds a stretchable space after the map
        mainLayout.addLayout(self.mapLayout)

        # Search Bars
        searchLayout = QHBoxLayout()
        
        # State ComboBox with "Select All" option
        self.stateLabel = QLabel('State:')
        self.stateComboBox = QComboBox()
        self.stateComboBox.addItem("Select All")
        self.stateComboBox.addItems(self.df['State'].unique())
        
        # County ComboBox with "Select All" option
        self.countyLabel = QLabel('County:')
        self.countyComboBox = QComboBox()
        self.countyComboBox.addItem("Select All")

        # Add widgets with spacers in between to the searchLayout
        searchLayout.addWidget(self.stateLabel)
        searchLayout.addWidget(self.stateComboBox, 1)  # Set stretch factor for State ComboBox to 1
        searchLayout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Fixed))
        searchLayout.addWidget(self.countyLabel)
        searchLayout.addWidget(self.countyComboBox, 2)  # Set stretch factor for County ComboBox to 2
        
        # self.zipLabel = QLabel('ZIP:')
        self.zipComboBox = QComboBox()
        searchLayout.addWidget(self.stateLabel)
        searchLayout.addWidget(self.stateComboBox)
        searchLayout.addWidget(self.countyLabel)
        searchLayout.addWidget(self.countyComboBox)
        # searchLayout.addWidget(self.zipLabel)
        # searchLayout.addWidget(self.zipComboBox)
        mainLayout.addLayout(searchLayout)

        # Filters
        filtersLayout = QFormLayout()
        self.gradeModel = QStandardItemModel()
        select_all_item = QStandardItem("Select All")
        select_all_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        select_all_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.gradeModel.appendRow(select_all_item)

        for grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']:
            item = QStandardItem(grade)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            self.gradeModel.appendRow(item)

        self.gradeComboBox = QComboBox()
        self.gradeComboBox.setModel(self.gradeModel)
        self.gradeComboBox.setView(QListView(self))
        self.gradeComboBox.view().clicked.connect(self.handleItemPressed)
        self.gradeComboBox.setEditText("Select Grades")
        
        # Adjust the size of gradeComboBox
        self.gradeComboBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.gradeComboBox.setMaximumWidth(200)
        filtersLayout.addRow('Violent Crime Grade:', self.gradeComboBox)

        # Median Home Price Filter
        self.homePriceMinInput = QLineEdit()
        self.homePriceMaxInput = QLineEdit()
        self.homePriceMinInput.setMaximumWidth(100)
        self.homePriceMaxInput.setMaximumWidth(100)

        homePriceLayout = QHBoxLayout()
        homePriceLayout.addWidget(QLabel('Min:'))
        homePriceLayout.addWidget(self.homePriceMinInput)
        homePriceLayout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Fixed))
        homePriceLayout.addWidget(QLabel('Max:'))
        homePriceLayout.addWidget(self.homePriceMaxInput)
        homePriceLayout.addStretch(1)  # Add stretch to right-align the items
        filtersLayout.addRow('Median Home Price:', homePriceLayout)

        # Monthly Payment Filter
        self.monthlyPaymentMinInput = QLineEdit()
        self.monthlyPaymentMaxInput = QLineEdit()
        self.monthlyPaymentMinInput.setMaximumWidth(100)
        self.monthlyPaymentMaxInput.setMaximumWidth(100)

        monthlyPaymentLayout = QHBoxLayout()
        monthlyPaymentLayout.addWidget(QLabel('Min:'))
        monthlyPaymentLayout.addWidget(self.monthlyPaymentMinInput)
        monthlyPaymentLayout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Fixed))
        monthlyPaymentLayout.addWidget(QLabel('Max:'))
        monthlyPaymentLayout.addWidget(self.monthlyPaymentMaxInput)
        monthlyPaymentLayout.addStretch(1)  # Add stretch to right-align the items
        filtersLayout.addRow('Monthly Payment:', monthlyPaymentLayout)

        # Ordinal Rank Filter (Sort ComboBox)
        self.sortRankComboBox = QComboBox()
        self.sortRankComboBox.addItems(["Unsorted", "Lowest to Highest", "Highest to Lowest"])
        
        # Adjust the size of sortRankComboBox
        self.sortRankComboBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.sortRankComboBox.setMaximumWidth(200)
        
        filtersLayout.addRow('Sort by Rank:', self.sortRankComboBox)

        mainLayout.addLayout(filtersLayout)

        # Search Button and Reset Button layout
        buttonContainerLayout = QHBoxLayout()  # This will contain our vertical layout
        buttonLayout = QVBoxLayout()  # Use QVBoxLayout to stack buttons vertically
        
        self.searchButton = QPushButton('Search')
        self.resetButton = QPushButton('Reset')
        self.resetButton.clicked.connect(self.resetFilters)
        
        # Add buttons to the vertical layout
        buttonLayout.addWidget(self.searchButton)
        buttonLayout.addWidget(self.resetButton)

        # Add the vertical layout to the horizontal layout and center it
        buttonContainerLayout.addStretch(1)
        buttonContainerLayout.addLayout(buttonLayout)
        buttonContainerLayout.addStretch(1)

        mainLayout.addLayout(buttonContainerLayout)

        # Realtor and Zillow Links section
        self.realtorZillowLayout = QVBoxLayout()

        self.stateInfoLabel = QLabel("State: ")
        self.countyInfoLabel = CustomLabel("County: ")
        self.countyInfoLabel.textChanged.connect(self.update_map_based_on_label)

        self.zipInfoLabel = QLabel("ZIP: ")

        self.realtorZillowLayout.addWidget(self.stateInfoLabel)
        self.realtorZillowLayout.addWidget(self.countyInfoLabel)
        self.realtorZillowLayout.addWidget(self.zipInfoLabel)

        # # Using the custom label for countyInfoLabel
        # self.countyInfoLabel = CustomLabel("County: ")
        self.countyInfoLabel.textChanged.connect(self.update_map_based_on_label)

        # Links
        self.realtorCountyStateLinkButton = QPushButton("Realtor (County Search)")
        self.realtorCountyStateLinkButton.clicked.connect(self.openRealtorCountyStateLink)

        self.realtorZipLinkButton = QPushButton("Realtor (ZIP Search)")
        self.realtorZipLinkButton.clicked.connect(self.openRealtorZipLink)

        self.zillowCountyStateLinkButton = QPushButton("Zillow (County Search)")
        self.zillowCountyStateLinkButton.clicked.connect(self.openZillowCountyStateLink)

        self.zillowZipLinkButton = QPushButton("Zillow (ZIP Search)")
        self.zillowZipLinkButton.clicked.connect(self.openZillowZipLink)

        # Create horizontal layouts for the buttons
        countyLinkLayout = QHBoxLayout()
        countyLinkLayout.addWidget(self.realtorCountyStateLinkButton)
        countyLinkLayout.addWidget(self.zillowCountyStateLinkButton)
        self.realtorZillowLayout.addLayout(countyLinkLayout)

        zipLinkLayout = QHBoxLayout()
        zipLinkLayout.addWidget(self.realtorZipLinkButton)
        zipLinkLayout.addWidget(self.zillowZipLinkButton)
        self.realtorZillowLayout.addLayout(zipLinkLayout)

        mainLayout.addLayout(self.realtorZillowLayout)

        # Tables
        self.s8FMRTable = QTableWidget()
        self.s8FMRTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.locationInfoTable = QTableWidget()
        self.locationInfoTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.s8CrimeGradeTable = QTableWidget()
        self.s8CrimeGradeTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.allDataTable = QTableWidget()
        self.allDataTable.setEditTriggers(QTableWidget.NoEditTriggers)
        
        mainLayout.addWidget(QLabel('\nS8 FMR - Click on the column headers to sort any table!'))
        mainLayout.addWidget(self.s8FMRTable)
        
        mainLayout.addWidget(QLabel('Location Info - Click on a row to update the Realtor and Zillow links as well as the map!'))
        mainLayout.addWidget(self.locationInfoTable)
        

        self.crimeGradeButton = QPushButton("Crime Grade Link")
        self.crimeGradeButton.clicked.connect(self.openCrimeGradeLink)

        mainLayout.addWidget(QLabel('S8 Crime Grade'))
        crimeGradeLayout = QVBoxLayout()
        crimeGradeLayout.addWidget(self.s8CrimeGradeTable)
        crimeGradeLayout.addWidget(self.crimeGradeButton)
        mainLayout.addLayout(crimeGradeLayout)

        
        mainLayout.addWidget(QLabel('All Data'))
        mainLayout.addWidget(self.allDataTable)

        scroll.setWidget(centralWidget)

        # Connect events
        self.stateComboBox.currentTextChanged.connect(self.updateCountyComboBox)
        self.countyComboBox.currentTextChanged.connect(self.updateZipComboBox)
        self.searchButton.clicked.connect(self.updateTables)

        self.locationInfoTable.cellClicked.connect(self.updateLinkInfo)

        # Synchronize scroll bars after initializing the tables
        self.synchronizeScrollBars()

        # Define the colors from the suggested theme
        primary_color = QColor("#001F3F")
        secondary_color = QColor("#0074D9")
        tertiary_color = QColor("#FFD700")
        background_color = QColor("#F7F7F7")
        text_color = QColor("#283238")
        
        # Apply the color palette
        palette = QPalette()
        palette.setColor(QPalette.Window, background_color)
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))  # Background color for text entry widgets
        palette.setColor(QPalette.AlternateBase, QColor("#F0F0F0"))  # Used as the alternate background color in views with alternating row colors
        palette.setColor(QPalette.Button, primary_color)
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))  # White text on buttons for contrast
        palette.setColor(QPalette.Highlight, secondary_color)  # Color for the highlighted items
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))  # Text color for highlighted items
        palette.setColor(QPalette.ToolTipBase, primary_color)
        palette.setColor(QPalette.ToolTipText, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        # Apply fonts
        header_font = QFont("Lato", 12, QFont.Bold)
        body_font = QFont("Lato", 10)
        
        # Set application-wide fonts (can be overridden for individual widgets)
        QApplication.setFont(body_font)
        
        # Applying font to specific widgets
        self.stateLabel.setFont(header_font)
        self.countyLabel.setFont(header_font)
        
        # Styling tables for better readability
        for table in [self.s8FMRTable, self.locationInfoTable, self.s8CrimeGradeTable, self.allDataTable]:
            table.setAlternatingRowColors(True)  # Stripe rows
            table.setStyleSheet("selection-background-color: #0074D9;")  # Use secondary color for selected row
        
        # Styling buttons and comboboxes
        button_style = """
        QPushButton {
            background-color: #001F3F;
            color: #FFFFFF;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #0074D9;
        }
        QComboBox {
            padding: 5px;
            border: 1px solid #001F3F;
            border-radius: 4px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            selection-background-color: #0074D9;
            selection-color: #FFFFFF;
        }
        """
        self.setStyleSheet(button_style)
        
        # Adjusting layout spacings for a cleaner look
        self.layout().setSpacing(15)
        self.layout().setContentsMargins(10, 10, 10, 10)


        self.s8FMRTable.setSortingEnabled(True)
        self.locationInfoTable.setSortingEnabled(True)
        self.s8CrimeGradeTable.setSortingEnabled(True)
        self.allDataTable.setSortingEnabled(True)

        mainLayout.addSpacing(650)  # Adds pixels of dead space at the end

    def openCrimeGradeLink(self):
        # Fetch the ZIP code from the currently selected row in the table
        row = self.locationInfoTable.currentRow()
        if row == -1:  # No row selected
            QMessageBox.warning(self, "No Selection", "Please select a row in the table to get the ZIP code.")
            return
        
        zipcode = self.locationInfoTable.item(row, 2).text()
        
        # Format the link
        link = f"https://crimegrade.org/safest-places-in-{zipcode}/"
        
        # Open the link in the default web browser
        webbrowser.open(link)

    
    def synchronizeScrollBars(self):
        # This function ensures that the vertical scrolling of one table affects all tables.
        def sync_scroll(value):
            self.s8FMRTable.verticalScrollBar().setValue(value)
            self.locationInfoTable.verticalScrollBar().setValue(value)
            self.s8CrimeGradeTable.verticalScrollBar().setValue(value)
            self.allDataTable.verticalScrollBar().setValue(value)

        # Connect the scroll bars' valueChanged signal to sync_scroll function
        self.s8FMRTable.verticalScrollBar().valueChanged.connect(sync_scroll)
        self.locationInfoTable.verticalScrollBar().valueChanged.connect(sync_scroll)
        self.s8CrimeGradeTable.verticalScrollBar().valueChanged.connect(sync_scroll)
        self.allDataTable.verticalScrollBar().valueChanged.connect(sync_scroll)

    def resetFilters(self):
        # Reset ComboBoxes
        self.stateComboBox.setCurrentIndex(0)
        self.countyComboBox.setCurrentIndex(0)
        self.zipComboBox.clear()

        # Uncheck all grades in the gradeModel
        for i in range(self.gradeModel.rowCount()):
            self.gradeModel.item(i).setCheckState(Qt.Unchecked)
        self.gradeComboBox.setEditText("Select Grades")

        # Clear price and payment filters
        self.homePriceMinInput.clear()
        self.homePriceMaxInput.clear()
        self.monthlyPaymentMinInput.clear()
        self.monthlyPaymentMaxInput.clear()

        # Reset sort rank ComboBox
        self.sortRankComboBox.setCurrentIndex(0)
        
        # Clear all tables
        self.s8FMRTable.setRowCount(0)
        self.locationInfoTable.setRowCount(0)
        self.s8CrimeGradeTable.setRowCount(0)
        self.allDataTable.setRowCount(0)
        
         # Reset the Realtor and Zillow links section
        self.stateInfoLabel.setText("State: ")
        self.countyInfoLabel.setText("County: ")
        self.zipInfoLabel.setText("ZIP: ")

        # Reset the map to the USA view
        m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
        m.save(map_file_path)
        self.mapView.load(QUrl.fromLocalFile(map_file_path))

        


    def updateCountyComboBox(self):
        state_selected = self.stateComboBox.currentText()
        self.countyComboBox.clear()
        self.countyComboBox.addItem("Select All")
        if state_selected != "Select All":
            counties = self.df[self.df['State'] == state_selected]['County'].unique()
            self.countyComboBox.addItems(counties)

    def updateZipComboBox(self):
        county_selected = self.countyComboBox.currentText()
        self.zipComboBox.clear()
        if county_selected != "Select All":
            zips = self.df[self.df['County'] == county_selected]['ZIP'].unique()
            self.zipComboBox.addItems(map(str, zips))

    def handleItemPressed(self, index):
        item = self.gradeModel.itemFromIndex(index)

        # If "Select All" is checked/unchecked
        if item.text() == "Select All":
            new_state = Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
            item.setCheckState(new_state)
            for i in range(1, self.gradeModel.rowCount()):  # Start from 1 to skip "Select All"
                self.gradeModel.item(i).setCheckState(new_state)
        # If any other grade is checked/unchecked
        else:
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)

            # If all grades are checked, also check "Select All"
            if all([self.gradeModel.item(i).checkState() == Qt.Checked for i in range(1, self.gradeModel.rowCount())]):
                self.gradeModel.item(0).setCheckState(Qt.Checked)
            else:
                self.gradeModel.item(0).setCheckState(Qt.Unchecked)

        self.updateGradeComboBoxText()

    def updateGradeComboBoxText(self):
        selected_grades = []
        for i in range(self.gradeModel.rowCount()):
            if self.gradeModel.item(i).checkState() == Qt.Checked:
                selected_grades.append(self.gradeModel.item(i).text())
        if "Select All" in selected_grades:
            selected_grades.remove("Select All")
        if not selected_grades:
            self.gradeComboBox.setEditText("Select Grades")
        else:
            self.gradeComboBox.setEditText(", ".join(selected_grades))

    def updateTables(self):
        filtered_df = self.df.copy()

        # Filter based on State, County, and ZIP
        state_selected = self.stateComboBox.currentText()
        county_selected = self.countyComboBox.currentText()
        zip_selected = self.zipComboBox.currentText()
        if state_selected and state_selected != "Select All":
            filtered_df = filtered_df[filtered_df['State'] == state_selected]
        if county_selected and county_selected != "Select All":
            filtered_df = filtered_df[filtered_df['County'] == county_selected]
        if zip_selected:
            filtered_df = filtered_df[filtered_df['ZIP'] == int(zip_selected)]

        # Filter based on checked Violent Crime Grades
        selected_grades = []
        for i in range(1, self.gradeModel.rowCount()):  # Start from 1 to skip "Select All"
            if self.gradeModel.item(i).checkState() == Qt.Checked:
                selected_grades.append(self.gradeModel.item(i).text())
        if selected_grades:
            filtered_df = filtered_df[filtered_df['Total_Violent_Crime_Grade'].isin(selected_grades)]

        # Filter based on Median Home Price range
        min_home_price = self.homePriceMinInput.text()
        max_home_price = self.homePriceMaxInput.text()
        if min_home_price:
            filtered_df = filtered_df[filtered_df['Median Home Price Q1 2023'] >= float(min_home_price)]
        if max_home_price:
            filtered_df = filtered_df[filtered_df['Median Home Price Q1 2023'] <= float(max_home_price)]

        # Filter based on Monthly Payment range
        min_payment = self.monthlyPaymentMinInput.text()
        max_payment = self.monthlyPaymentMaxInput.text()
        if min_payment:
            filtered_df = filtered_df[filtered_df['Monthly Payment Q1 2023'] >= float(min_payment)]
        if max_payment:
            filtered_df = filtered_df[filtered_df['Monthly Payment Q1 2023'] <= float(max_payment)]

        # Apply sorting based on Rank
        sort_order = self.sortRankComboBox.currentText()
        if sort_order == "Lowest to Highest":
            filtered_df = filtered_df.sort_values(by="Investment Rank", ascending=True)
        elif sort_order == "Highest to Lowest":
            filtered_df = filtered_df.sort_values(by="Investment Rank", ascending=False)

        if not filtered_df.empty:
            self.stateInfoLabel.setText("State: " + filtered_df.iloc[0]['State'])
            self.countyInfoLabel.setText("County: " + filtered_df.iloc[0]['County'])
            self.zipInfoLabel.setText("ZIP: " + str(filtered_df.iloc[0]['ZIP']))
        else:
            self.stateInfoLabel.setText("State: ")
            self.countyInfoLabel.setText("County: ")
            self.zipInfoLabel.setText("ZIP: ")

        self.populateTables(filtered_df)
    
    # New methods to handle opening Realtor and Zillow links
    def openRealtorCountyStateLink(self):
        state = self.stateInfoLabel.text().replace("State: ", "")
        county = self.countyInfoLabel.text().replace("County: ", "")
        link = f"https://www.realtor.com/realestateandhomes-search/{county.replace(' ', '-')}_{state}/type-single-family-home"
        QDesktopServices.openUrl(QUrl(link))

    def openRealtorZipLink(self):
        zip_code = self.zipInfoLabel.text().replace("ZIP: ", "")
        link = f"https://www.realtor.com/realestateandhomes-search/{zip_code}/type-single-family-home"
        QDesktopServices.openUrl(QUrl(link))

    def openZillowCountyStateLink(self):
        state = self.stateInfoLabel.text().replace("State: ", "")
        county = self.countyInfoLabel.text().replace("County: ", "")
        link = f"https://www.zillow.com/homes/{county}-{state}_rb/"
        QDesktopServices.openUrl(QUrl(link))

    def openZillowZipLink(self):
        zip_code = self.zipInfoLabel.text().replace("ZIP: ", "")
        link = f"https://www.zillow.com/homes/{zip_code}_rb/"
        QDesktopServices.openUrl(QUrl(link))

    def updateLinkInfo(self, row, column):
        state = self.locationInfoTable.item(row, 0).text()  # Assuming State is the first column
        county = self.locationInfoTable.item(row, 1).text()  # Assuming County is the second column
        zip_code = self.df[(self.df['State'] == state) & (self.df['County'] == county)]['ZIP'].values[0]

        self.stateInfoLabel.setText("State: " + state)
        self.countyInfoLabel.setText("County: " + county)
        self.zipInfoLabel.setText("ZIP: " + str(zip_code))


    def populateTables(self, filtered_df):
        # Populate the tables with the filtered data
        fmr_columns = ['County', 'Efficiency', 'One-Bedroom', 'Two-Bedroom', 'Three-Bedroom', 
                       'Four-Bedroom', 'Monthly Payment Q1 2023', 'S8 rent - Mortgage Payment', 'Median Home Price Q1 2023', 'Investment Rank']
        self.populateTable(self.s8FMRTable, filtered_df, fmr_columns)

        location_columns = ['State', 'County', 'ZIP', 'Population (2020 census)', 'Density (Population/mi^2)', 
                            'Population Change Percent 2021-2022', 'Landlord Friendly', 'Investment Rank']
        self.populateTable(self.locationInfoTable, filtered_df, location_columns)

        crime_columns = ['County', 'Total_Violent_Crime_Grade', 'Total_Property_Crime_Grade', 
                         'Total_Other_Rate_Grade', 'Investment Rank']
        self.populateTable(self.s8CrimeGradeTable, filtered_df, crime_columns)

        # New All Data columns
        all_data_columns = ["State", "County", "Efficiency", "One-Bedroom", "Two-Bedroom", "Three-Bedroom", 
                            "Four-Bedroom", "ZIP", "Population (2020 census)", "Area (mi^2)", 
                            "Density (Population/mi^2)", "Total Population Change, Annual Change, July 1, 2021 to July 1, 2022", 
                            "Total Population Change, Cumulative Change, April 1, 2020 to July 1, 2022", 
                            "Population Change Percent 2021-2022", "Assault crimes per 1,000", "Robbery crimes per 1,000", 
                            "Rape crimes per 1,000", "Murder crimes per 1,000", "Theft crimes per 1,000", 
                            "Vehicle_Theft crimes per 1,000", "Burglary crimes per 1,000", "Arson crimes per 1,000", 
                            "Kidnapping crimes per 1,000", "Drug_Crimes crimes per 1,000", "Vandalism crimes per 1,000", 
                            "Identity_Theft crimes per 1,000", "Animal_Cruelty crimes per 1,000", "Total_Violent_Crime_Value crimes per 1,000", 
                            "Total_Violent_Crime_Grade", "Total_Property_Crime_Value crimes per 1,000", "Total_Property_Crime_Grade", 
                            "Total_Other_Rate_Value", "Total_Other_Rate_Grade", "Median Home Price Q1 2023", "Monthly Payment Q1 2023", 
                            "Monthly Payment Q1 2022", "Percent Change in Monthly Payment", "Average_S8_Rent", 
                            "S8 rent - Mortgage Payment", "Landlord Friendly", "Investment_Score", "Investment Rank"
                            ]
        self.populateTable(self.allDataTable, filtered_df, all_data_columns)

    def populateTable(self, table, df, columns):
        table.setSortingEnabled(False)  # Step 1: Temporarily disable sorting
        
        table.setRowCount(0)  # Clear the table
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        for index, row in df.iterrows():
            table.insertRow(table.rowCount())
            for i, column in enumerate(columns):
                item_text = str(row[column])
                item = CustomTableWidgetItem(item_text)
                item.setToolTip(item_text)  # Setting tooltip for each cell
                table.setItem(table.rowCount() - 1, i, item)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.resizeColumnsToContents()

        # Adjust column width to fit content and enable horizontal scrolling
        table.resizeColumnsToContents()
        table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)  # Smooth horizontal scrolling

        # Adjust the height of the horizontal header to fit the content
        header = table.horizontalHeader()
        header.setMinimumHeight(50)  # Set a reasonable minimum height for the header
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align header text to the left and vertically center
        font_metrics = QFontMetrics(self.font())
        max_header_height = max([font_metrics.boundingRect(col).height() for col in columns])
        header.setFixedHeight(max_header_height + 10)  # Add a little padding

        # Adjust column width to fit content and enable horizontal scrolling
        for i in range(table.columnCount()):
            column_width = table.columnWidth(i)
            table.setColumnWidth(i, column_width * 2)  # Double the width of each column

        if table == self.allDataTable:  # Apply changes only to the "All Data" table
            header = table.horizontalHeader()
            header.setDefaultSectionSize(header.defaultSectionSize() * 2)  # Double the default header height
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
                
        # Adjust the height of the table to show up to 5 rows
        num_rows_to_display = min(5, table.rowCount())
        table.setFixedHeight(self.DEFAULT_ROW_HEIGHT * num_rows_to_display + table.horizontalHeader().height())

        table.setSortingEnabled(True)  # Step 3: Re-enable sorting
       
    def update_map_based_on_label(self, county_name):
        # Extract county name from the signal
        county_name = county_name.replace("County: ", "").strip()
        
        # If there's no county name, do nothing
        if not county_name:
            return

        # Look up coordinates for the county from the s8_investment dataframe
        county_data = self.df[self.df['County'] == county_name]
        if county_data.empty:
            # If county not found in dataset, do nothing or show an error
            return

        # Get the coordinates and other details
        lat = county_data['Latitude'].iloc[0]
        lon = county_data['Longitude'].iloc[0]
        one_bedroom = "${:,.2f}".format(county_data['One-Bedroom'].iloc[0])
        two_bedroom = "${:,.2f}".format(county_data['Two-Bedroom'].iloc[0])
        three_bedroom = "${:,.2f}".format(county_data['Three-Bedroom'].iloc[0])
        four_bedroom = "${:,.2f}".format(county_data['Four-Bedroom'].iloc[0])
        median_home_price = "${:,.2f}".format(county_data['Median Home Price Q1 2023'].iloc[0])
        s8rent_mortgage_payment = "${:,.2f}".format(county_data['S8 rent - Mortgage Payment'].iloc[0])
        crime_grade = county_data['Total_Violent_Crime_Grade'].iloc[0]
        population = county_data['Population (2020 census)'].iloc[0]
        investment_rank = county_data['Investment Rank'].iloc[0]

        # Format the popup content
        popup_content = f"""
        <div style="padding: 5px; line-height: 1.3; font-size: 1.4em;">
            <strong style="font-size: 1.9em; text-align: center; display: block;">{county_name}</strong><br><br>
            <span style="font-weight: bold;">One-Bedroom:</span> {one_bedroom}<br>
            <span style="font-weight: bold;">Two-Bedroom:</span> {two_bedroom}<br>
            <span style="font-weight: bold;">Three-Bedroom:</span> {three_bedroom}<br>
            <span style="font-weight: bold;">Four-Bedroom:</span> {four_bedroom}<br>
            <span style="font-weight: bold;">Median Home Price (Q1 2023):</span> {median_home_price}<br>
            <span style="font-weight: bold;">S8 rent - Mortgage Payment:</span> {s8rent_mortgage_payment}<br>
            <span style="font-weight: bold;">Violent Crime Grade:</span> {crime_grade}<br>
            <span style="font-weight: bold;">Population (2020 census):</span> {population}<br>
            <span style="font-weight: bold;">Investment Rank:</span> {investment_rank}
        </div>
        """

        # Create a new folium map centered on the selected county
        m = folium.Map(location=[lat, lon], zoom_start=8)

        # Add a circle marker for the selected county
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            popup=folium.Popup(popup_content, max_width=350),
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6
        ).add_to(m)

        m.save(map_file_path)

        # Load the new map into the QWebEngineView
        self.mapView.load(QUrl.fromLocalFile(map_file_path))


if __name__ == '__main__':
    # df_s8 = pd.read_csv("/mnt/data/s8_investment.csv")
    # df_s8 = pd.read_csv("s8_investment.csv")
    df_s8 = pd.read_csv(csv_file_path)
    app = QApplication([])
    mainWindow = S8App(df_s8)
    mainWindow.show()
    app.exec_()