from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QRadioButton, QFrame, QMessageBox, QGridLayout, QHBoxLayout, QDialog, QCheckBox
from PyQt6.QtCore import Qt
import psycopg2
from database import connect_to_database
from utils import confirmation_dialog
from gene_label import GeneLabel
from itertools import cycle

class GeneApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gene Mapping App")
        self.setGeometry(100, 100, 600, 700)
        self.setWindowIcon(QIcon('icon.png'))

        self.connection, self.cursor = connect_to_database()

        self.chromosomes = {}
        self.color_cycles = {}
        self.gene_counter = 0  # Counter unique tab names

        self.create_widgets()
        self.create_menu()

        self.update_visualizer()

    def create_widgets(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create Notebook (Tabs)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create Overview tab
        self.overview_frame = QWidget()
        self.tabs.addTab(self.overview_frame, "Overview")
        self.create_overview_widgets()

    def create_menu(self):
        menu_bar = self.menuBar()
        info_menu = menu_bar.addMenu("About")
        info_menu.aboutToShow.connect(self.show_info_page)

    def show_info_page(self):
        info_msg = QMessageBox(self)
        info_msg.setWindowTitle("About Gene Visualiser App")
        info_msg.setText("SKJ project\nVersion: 4.0\nAuthor: PYT0031")
        info_msg.exec()

    def open_gene_tab(self, chromosome, region, gene):
        if (chromosome, region, gene) in self.gene_labels:
            gene_label = self.gene_labels[(chromosome, region, gene)]
            if gene_label.active:
                self.create_gene_tab(chromosome, region, gene)
            else:
                print("Gene label is inactive and cannot be opened.")
        else:
            print("Gene label not found.")

    def create_overview_widgets(self):
        layout = QVBoxLayout(self.overview_frame)

        # Form layout
        form_layout = QGridLayout()

        self.chromosome_entry = QLineEdit()
        form_layout.addWidget(QLabel("Chromosome:"), 0, 0)
        form_layout.addWidget(self.chromosome_entry, 0, 1)

        self.region_entry = QLineEdit()
        form_layout.addWidget(QLabel("Region:"), 1, 0)
        form_layout.addWidget(self.region_entry, 1, 1)

        self.gene_entry = QLineEdit()
        form_layout.addWidget(QLabel("Gene:"), 2, 0)
        form_layout.addWidget(self.gene_entry, 2, 1)

        layout.addLayout(form_layout)

        # Button layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Gene")
        self.delete_chromosome_button = QPushButton("Delete Chromosome")
        self.delete_region_button = QPushButton("Delete Region")
        self.delete_gene_button = QPushButton("Delete Gene")
        self.search_gene_button = QPushButton("Search Gene")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_chromosome_button)
        button_layout.addWidget(self.delete_region_button)
        button_layout.addWidget(self.delete_gene_button)
        button_layout.addWidget(self.search_gene_button)
        layout.addLayout(button_layout)

        # Visual separator of filters
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Filters layout
        filters_layout = QHBoxLayout()
        self.filter_radio1 = QRadioButton("Radiation prone")
        self.filter_radio2 = QRadioButton("Methylation prone")
        filters_layout.addWidget(QLabel("Filters:"))
        filters_layout.addWidget(self.filter_radio1)
        filters_layout.addWidget(self.filter_radio2)
        layout.addLayout(filters_layout)

        # Connect filter changes
        self.filter_radio1.toggled.connect(self.update_visualizer)
        self.filter_radio2.toggled.connect(self.update_visualizer)

        # Chromosome Visualizer (Canvas)
        self.chromosome_canvas = QFrame()
        self.chromosome_canvas.setFrameStyle(QFrame.Shape.Box)
        layout.addWidget(self.chromosome_canvas)

        self.chromosome_layout = QVBoxLayout(self.chromosome_canvas)
        self.chromosome_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chromosome_layout.setSpacing(10)

        # Connect add_gene method to Add Gene button
        self.add_button.clicked.connect(self.add_gene)
        self.delete_chromosome_button.clicked.connect(self.delete_chromosome)
        self.delete_region_button.clicked.connect(self.delete_region)
        self.delete_gene_button.clicked.connect(self.delete_gene)

        # Connect search_gene function to the Search Gene button
        self.search_gene_button.clicked.connect(self.search_gene)

    def add_gene(self):
        chromosome = self.chromosome_entry.text()
        region = self.region_entry.text()
        gene = self.gene_entry.text()

        if chromosome and region and gene:
            try:
                self.cursor.execute("INSERT INTO genes (chromosome, region, gene_name) VALUES (%s, %s, %s)",
                                    (chromosome, region, gene))
                self.connection.commit()
                print("Gene added successfully")

                # Update visualizer after successfully adding the gene
                self.update_visualizer()

            except (Exception, psycopg2.Error) as error:
                print("Error inserting gene into the database:", error)
                self.connection.rollback()

        else:
            QMessageBox.critical(self, "Error", "Chromosome, region, and gene name cannot be empty.")

    def update_visualizer(self):
        # Clear existing labels and layouts (duplicates and / or filtering)
        for i in reversed(range(self.chromosome_layout.count())):
            item = self.chromosome_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                layout = item.layout()
                if layout:
                    layout.deleteLater()

        # Get filter states
        radiation_prone = self.filter_radio1.isChecked()
        methylation_prone = self.filter_radio2.isChecked()

        max_x = 0
        max_y = 0

        # Fetch gene data from the database
        try:
            self.cursor.execute("SELECT chromosome, region, gene_name, methylation_prone, radiation_prone FROM genes")
            gene_data = self.cursor.fetchall()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving gene data from the database:", error)
            return

        # Store references to gene labels and colored boxes (only GUI related stuff basically)
        self.gene_labels = {}
        chromosome_labels = {}  # Store chromosome labels to avoid duplication
        region_labels = {}  # Store region labels to avoid duplication
        gene_layouts = {}  # Store gene layouts by chromosome and region

        # Store positions of region labels
        region_positions = {}

        # Process fetched data and update visualizer
        for chrom, reg, gene, methylation_prone_db, radiation_prone_db in gene_data:
            self.color_cycles.setdefault(chrom, cycle(["red", "green", "blue", "orange", "purple"]))

            # Create chromosome and region labels if not already created
            if chrom not in chromosome_labels:
                chromosome_label = QLabel(chrom)
                chromosome_label.setStyleSheet("font-weight: bold;")
                self.chromosome_layout.addWidget(chromosome_label)
                max_y += 20
                chromosome_labels[chrom] = chromosome_label

            if reg not in region_labels:
                region_label = QLabel(reg)
                region_label.setStyleSheet("margin-left: 20px;")
                self.chromosome_layout.addWidget(region_label)
                max_y += 20
                region_labels[reg] = region_label

                # Store position of region label
                region_positions[reg] = max_y

            else:
                # If region label exists, use its position
                max_y = region_positions[reg]

            # Create gene layout if not already created
            if (chrom, reg) not in gene_layouts:
                gene_layouts[(chrom, reg)] = QHBoxLayout()
                self.chromosome_layout.addLayout(gene_layouts[(chrom, reg)])

            gene_layout = gene_layouts[(chrom, reg)]

            # Create gene label if gene is not None
            if gene is not None:
                gene_label = QLabel(gene)
                color = next(self.color_cycles[chrom])
                gene_label.setStyleSheet(
                    f"background-color: {color}; color: white; border: 1px solid black; text-align: center;")
                gene_label.setFixedSize(80, 20)
                gene_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text

                # Store chromosome and region with gene label
                gene_label.chromosome = chrom
                gene_label.region = reg

                # Adjust color based on filter states and gene properties
                if (methylation_prone and radiation_prone_db) or (radiation_prone and methylation_prone_db):
                    gene_label.setStyleSheet(
                        "background-color: gray; color: white; border: 1px solid black; text-align: center;")
                    gene_label.active = False  # Mark as inactive
                else:
                    gene_label.active = True  # Mark as active

                # Connect gene label click event to open_gene_tab method
                gene_label.mousePressEvent = lambda event, ch=chrom, rg=reg, ge=gene: self.open_gene_tab(ch, rg, ge)

                self.chromosome_layout.addWidget(gene_label)
                max_x += 100
                max_y += 20

                # Store reference to gene label
                self.gene_labels[(chrom, reg, gene)] = gene_label

        max_y += 10  # Space between chromosomes

    def delete_chromosome(self):
        chromosome = self.chromosome_entry.text()
        if chromosome:
            confirmation = confirmation_dialog("Are you sure you want to delete this chromosome?")
            if confirmation == QMessageBox.StandardButton.Yes:
                try:
                    self.cursor.execute("DELETE FROM genes WHERE chromosome = %s", (chromosome,))
                    self.connection.commit()
                    print("Chromosome deleted successfully")
                except (Exception, psycopg2.Error) as error:
                    print("Error deleting chromosome from the database:", error)
                    self.connection.rollback()

                # Update visualizer after deleting chromosome
                self.update_visualizer()
        else:
            QMessageBox.critical(self, "Error", "Chromosome name cannot be empty.")

    def delete_region(self):
        chromosome = self.chromosome_entry.text()
        region = self.region_entry.text()
        if chromosome and region:
            confirmation = confirmation_dialog("Are you sure you want to delete this region?")
            if confirmation == QMessageBox.StandardButton.Yes:
                try:
                    # Update database records for genes in the specified region
                    self.cursor.execute(
                        "UPDATE genes SET region = NULL, gene_name = NULL, methylation_prone = FALSE, radiation_prone = FALSE, gene_text = '' WHERE chromosome = %s AND region = %s",
                        (chromosome, region))
                    self.connection.commit()
                    print("Region data updated successfully")
                except (Exception, psycopg2.Error) as error:
                    print("Error updating region data in the database:", error)
                    self.connection.rollback()

                # Update visualizer after deleting region
                self.update_visualizer()
        else:
            QMessageBox.critical(self, "Error", "Chromosome and region names cannot be empty.")

    def delete_gene(self):
        chromosome = self.chromosome_entry.text()
        region = self.region_entry.text()
        gene = self.gene_entry.text()
        if chromosome and region and gene:
            confirmation = confirmation_dialog("Are you sure you want to delete this gene?")
            if confirmation == QMessageBox.StandardButton.Yes:
                try:
                    # Update database records for the specified gene
                    self.cursor.execute(
                        "UPDATE genes SET gene_name = NULL, methylation_prone = FALSE, radiation_prone = FALSE, gene_text = '' WHERE chromosome = %s AND region = %s AND gene_name = %s",
                        (chromosome, region, gene))
                    self.connection.commit()
                    print("Gene data updated successfully")
                except (Exception, psycopg2.Error) as error:
                    print("Error updating gene data in the database:", error)
                    self.connection.rollback()

                # Update visualizer after deleting gene
                self.update_visualizer()
        else:
            QMessageBox.critical(self, "Error", "Chromosome, region, and gene names cannot be empty.")

    def confirmation_dialog(self, message):
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Confirmation")
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return dialog.exec()

    def search_gene(self):
        chromosome = self.chromosome_entry.text()
        region = self.region_entry.text()
        gene = self.gene_entry.text()
        if chromosome and region and gene:
            if (chromosome, region, gene) in self.gene_labels:
                gene_label = self.gene_labels[(chromosome, region, gene)]
                if gene_label.active:
                    try:
                        # Query the database to check if the gene exists for the specified chromosome and region
                        self.cursor.execute(
                            "SELECT COUNT(*) FROM genes WHERE chromosome = %s AND region = %s AND gene_name = %s",
                            (chromosome, region, gene))
                        count = self.cursor.fetchone()[0]
                        if count > 0:
                            # If the gene exists and is active, open its gene tab
                            self.create_gene_tab(chromosome, region, gene)
                            QMessageBox.information(self, "Search Result",
                                                    f"Gene '{gene}' found in chromosome '{chromosome}' and region '{region}'.")
                        else:
                            QMessageBox.information(self, "Search Result", f"Gene '{gene}' not found.")
                    except (Exception, psycopg2.Error) as error:
                        print("Error searching for gene in the database:", error)
                else:
                    QMessageBox.warning(self, "Inactive Gene", "Inactive gene cannot be opened.")
            else:
                QMessageBox.warning(self, "Gene Not Found", "Gene not found in database.")
        else:
            QMessageBox.critical(self, "Error", "Chromosome, region, and gene names cannot be empty.")

    def create_gene_tab(self, chromosome, region, gene):
        gene_tab = QWidget()
        gene_tab_layout = QVBoxLayout(gene_tab)

        # Chromosome, Region, Gene information
        gene_tab_layout.addWidget(QLabel(f"Chromosome: {chromosome}"))
        gene_tab_layout.addWidget(QLabel(f"Region: {region}"))
        gene_tab_layout.addWidget(QLabel(f"Gene: {gene}"))

        # Text input box
        text_box = QLineEdit()
        text_box.setFixedHeight(100)  # Set fixed height for the text box because Qt is being dumb
        gene_tab_layout.addWidget(text_box)

        # Load previously saved text from the database if available
        try:
            self.cursor.execute("SELECT gene_text FROM genes WHERE chromosome = %s AND region = %s AND gene_name = %s", (chromosome, region, gene))
            saved_text = self.cursor.fetchone()[0]
            text_box.setText(saved_text)
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving saved text from the database:", error)

        # Checkboxes
        checkbox_layout = QHBoxLayout()
        methylation_checkbox = QCheckBox("Methylation Prone")
        radiation_checkbox = QCheckBox("Radiation Prone")
        checkbox_layout.addWidget(methylation_checkbox)
        checkbox_layout.addWidget(radiation_checkbox)
        gene_tab_layout.addLayout(checkbox_layout)

        # Set checkbox states based on saved info
        try:
            self.cursor.execute("SELECT methylation_prone, radiation_prone FROM genes WHERE chromosome = %s AND region = %s AND gene_name = %s", (chromosome, region, gene))
            saved_info = self.cursor.fetchone()
            if saved_info:
                methylation_checkbox.setChecked(saved_info[0])
                radiation_checkbox.setChecked(saved_info[1])
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving saved checkbox states from the database:", error)

        # Store references to text box and checkboxes
        gene_tab.gene_text_box = text_box
        gene_tab.methylation_checkbox = methylation_checkbox
        gene_tab.radiation_checkbox = radiation_checkbox

        # Save and Close buttons for da gene tab
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        close_button = QPushButton("Close")
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)
        gene_tab_layout.addLayout(button_layout)

        # Adjust spacing
        gene_tab_layout.setSpacing(10)  # Vertical
        gene_tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align widgets

        self.tabs.addTab(gene_tab, gene)

        # Connect button clicks
        save_button.clicked.connect(
            lambda: self.save_gene_changes(chromosome, region, gene, text_box.text(), methylation_checkbox.isChecked(),
                                           radiation_checkbox.isChecked()))
        close_button.clicked.connect(lambda: self.close_gene_tab(gene_tab))

    def close_gene_tab(self, gene_tab):
        index = self.tabs.indexOf(gene_tab)
        if index != -1:
            self.tabs.removeTab(index)

    def save_gene_changes(self, chromosome, region, gene, text, methylation_prone, radiation_prone):
        # Check if gene data already exists
        try:
            self.cursor.execute("SELECT * FROM genes WHERE chromosome = %s AND region = %s AND gene_name = %s", (chromosome, region, gene))
            existing_data = self.cursor.fetchone()
        except (Exception, psycopg2.Error) as error:
            print("Error checking existing gene data in the database:", error)

        if existing_data:
            # Update gene data
            try:
                self.cursor.execute("UPDATE genes SET gene_text = %s, methylation_prone = %s, radiation_prone = %s WHERE chromosome = %s AND region = %s AND gene_name = %s", (text, methylation_prone, radiation_prone, chromosome, region, gene))
                self.connection.commit()
                print("Gene data updated successfully")
            except (Exception, psycopg2.Error) as error:
                print("Error updating gene data in the database:", error)
                self.connection.rollback()
        else:
            # Insert new gene data
            try:
                self.cursor.execute("INSERT INTO genes (chromosome, region, gene_name, gene_text, methylation_prone, radiation_prone) VALUES (%s, %s, %s, %s, %s, %s)", (chromosome, region, gene, text, methylation_prone, radiation_prone))
                self.connection.commit()
                print("New gene data inserted successfully")
            except (Exception, psycopg2.Error) as error:
                print("Error inserting new gene data into the database:", error)
                self.connection.rollback()

    def closeEvent(self, event):
        confirmation = confirmation_dialog("Are you sure you want to exit the application?")
        if confirmation == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

