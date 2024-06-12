import sqlite3

from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QTableWidgetItem, QTableWidget, QMessageBox
import sys
from PyQt5 import uic

TITLE = ['ID', 'СОРТ', 'ЗЁРНА/МОЛОТЫЙ', 'ОБЪЁМ в гр', 'ЦЕНА, руб.', 'СТЕПЕНЬ ОБЖАРКИ', 'ВКУС']
TITLE1 = ['СОРТ', 'СТЕПЕНЬ ОБЖАРКИ', 'ЗЁРНА/МОЛОТЫЙ', 'ОБЪЁМ в гр', 'ЦЕНА, руб.']
TITLE0 = list(map(lambda x: str(x), range(1, 7)))
SIZE = [1200, 600]
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.con = sqlite3.connect('coffee.sqlite')
        self.initUi()

    def initUi(self):
        self.pushButton_3.clicked.connect(self.clicker)
        self.setGeometry(300, 300, *SIZE)
        self.setWindowTitle('Капучино')
        self.statusBar().showMessage("This is status bar")
        cur = self.con.cursor()
        result = cur.execute("SELECT degree FROM degrees").fetchall()
        self.comboBox.addItems([item[0] for item in result])
        self.pushButton_2.clicked.connect(self.filter)
        self.pushButton.clicked.connect(self.run)

    def run(self):
        cur = self.con.cursor()
        try:
            if self.lineEdit.text():
                result = cur.execute(f"{self.lineEdit.text()}").fetchall()
            else:
                result = cur.execute(
                    """SELECT DISTINCT products.id, sorts_coffee.name, ground_beans, volume, price, degrees.degree, sorts_coffee.taste 
                    FROM sorts_coffee, degrees JOIN products
                    ON sorts_coffee.id_sort = products.id_sort AND
                    degrees.id = products.id_degree
                    ORDER BY sorts_coffee.name""").fetchall()
            self.tableWidget.setRowCount(len(result))
            self.tableWidget.setColumnCount(len(result[0]))
            if not self.lineEdit.text():
                self.tableWidget.setHorizontalHeaderLabels(TITLE)
            else:
                self.tableWidget.setHorizontalHeaderLabels(TITLE0)

            for i, elem in enumerate(result):
                for j, val in enumerate(elem):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
                    self.tableWidget.resizeColumnsToContents()
        except Exception as e:
            print(e)
            self.statusBar().showMessage(str(e))
            self.tableWidget.clearContents()

    def filter(self):
        cur = self.con.cursor()
        result = cur.execute(f"""
                    SELECT DISTINCT sorts_coffee.name, ground_beans, volume, price, degrees.degree, sorts_coffee.taste 
                    FROM sorts_coffee, degrees JOIN products
                    ON sorts_coffee.id_sort = products.id_sort AND
                    degrees.id = products.id_degree
                    WHERE id_degree = {self.comboBox.currentIndex() + 1}
                    """).fetchall()
        self.tableWidget.setRowCount(len(result))
        self.tableWidget.setColumnCount(len(result[0]))
        self.tableWidget.setHorizontalHeaderLabels(TITLE[1:])

        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
                self.tableWidget.resizeColumnsToContents()

    def clicker(self):
        win2 = EditTable()
        win2.show()
        win2.exec()



class EditTable(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('addEditCoffeeForm1.ui', self)
        self.con = sqlite3.connect("coffee.sqlite")
        self.initUi()

    def initUi(self):
        self.setWindowTitle('Edit')

        self.pushButton.clicked.connect(self.update_result)
        self.tableWidget.itemChanged.connect(self.item_changed)
        self.pushButton_2.clicked.connect(self.save_results)
        self.pushButton_3.clicked.connect(self.delete_elem)
        self.modified = {}
        self.titles = None
        cur = self.con.cursor()
        result = cur.execute("SELECT name FROM sorts_coffee").fetchall()
        self.comboBox.addItems([item[0] for item in result])
        result = cur.execute("SELECT degree FROM degrees").fetchall()
        self.comboBox_2.addItems([item[0] for item in result])
        self.comboBox_3.addItems([item for item in ['beans', 'ground']])


    def update_result(self):
        print(self.spinBox.text())
        cur = self.con.cursor()
        
        result = cur.execute("""SELECT sorts_coffee.name, degrees.degree, ground_beans, volume, price 
        FROM sorts_coffee, degrees INNER JOIN products
        ON sorts_coffee.id_sort = products.id_sort AND degrees.id = products.id_degree
        WHERE products.id=? """,
        (item_id := self.spinBox.text(),)).fetchall()

        self.tableWidget.setRowCount(len(result))
        if not result:
            self.label_2.setText('Запись не найдена')
            return
        else:
            self.label_2.setText(f'Запись с id {item_id} найдена ')
        self.tableWidget.setHorizontalHeaderLabels(TITLE1)
        self.tableWidget.setColumnCount(len(result[0]))
        self.titles = [description[0] for description in cur.description]
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
        self.modified = {}

    def item_changed(self, item):
        if item.column() in [2, 3, 4]:
            self.modified[self.titles[item.column()]] = item.text()
        print(item.column(), item.text(), self.titles[item.column()])
        print(self.modified)

    def save_results(self):
        if self.modified:
            cur = self.con.cursor()
            que = "UPDATE products SET\n"
            que += " ,".join([f"{key}='{self.modified.get(key)}'"
                              for key in self.modified.keys()])
            que += "WHERE id = ?"
            print(que)
            cur.execute(que, (self.spinBox.text(),))
            self.con.commit()
            self.modified.clear()

    def delete_elem(self):
        item_id = self.spinBox.text()
        valid = QMessageBox.question(
            self, '', "Действительно удалить элементы с id " + ",".join(item_id),
            QMessageBox.Yes, QMessageBox.No)
        # Если пользователь ответил утвердительно, удаляем элементы.
        # Не забываем зафиксировать изменения
        if valid == QMessageBox.Yes:
            cur = self.con.cursor()
            cur.execute("DELETE FROM products WHERE id = ?",
        (item_id,))
            self.con.commit()

    def accept(self):
        self.modified['id_sort'] = self.comboBox.currentIndex() + 1
        self.modified['id_degree'] = self.comboBox_2.currentIndex() + 1
        self.modified['ground_beans'] = 'beans'
        self.modified['volume'] = self.lineEdit.text()
        self.modified['price'] = self.lineEdit_2.text()
        print(self.modified)
        cur = self.con.cursor()
        que = """INSERT INTO products(id_sort, id_degree, ground_beans, volume, price)
                VALUES (2, 2, 'beans', 600, 2512)"""
        que = """INSERT INTO products(id_sort, id_degree, ground_beans, volume, price)
                        VALUES (?, ?, ?, ?, ?)"""
        cur.execute(que, [self.comboBox.currentIndex() + 1,
                          self.comboBox_2.currentIndex() + 1,
                          self.comboBox_3.currentText(),
                          self.lineEdit.text(),
                          self.lineEdit_2.text()])

        self.con.commit()
        print(self.modified)
        self.modified = {}
        self.done(0)

    def reject(self):
        self.label.setText('Cancel')
        print('reject')
        self.done(0)




def main():
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()