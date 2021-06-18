import sqlite3


def createBD_FromDump():
    cur = sqlite3.connect('db/db.db')
    f = open('db/db_dump.sql', 'r', encoding='UTF-8')
    dump = f.read()
    cur.executescript(dump)


class requestDB:

    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES(?) ", (user_id,))

    def get_users(self):
        with self.connection:
            self.cursor.execute("SELECT * FROM `users`")
            return self.cursor.fetchall()

    def add_admin(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `admins` (`user_id`) VALUES(?) ", (user_id,))

    def get_admins(self):
        with self.connection:
            self.cursor.execute("SELECT * FROM `admins`")
            return self.cursor.fetchall()

    def add_manufacturer_to_products_stack(self, user_id, manufacturer):
        with self.connection:
            return self.cursor.execute("INSERT INTO `products_stack` (`user_id`, `manufacturer`) VALUES(?,?) ", (user_id, manufacturer))

    def add_taste_to_products_stack(self, user_id, taste):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `products_stack` SET `taste`=? WHERE user_id=?", (taste, user_id))

    def add_puffs_to_products_stack(self, user_id, puffs):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `products_stack` SET `number_of_puffs`=? WHERE user_id=?", (puffs, user_id))

    def add_amount_to_products_stack(self, user_id, amount):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `products_stack` SET `amount`=? WHERE user_id=?", (amount, user_id))

    def get_manufacturer_from_products_stack(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT manufacturer FROM products_stack WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()

    def get_taste_from_products_stack(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT taste FROM products_stack WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()

    def get_puffs_from_products_stack(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT number_of_puffs FROM products_stack WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()

    def get_amount_from_products_stack(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT amount FROM products_stack WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()

    def delete_product_object_from_stack(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `products_stack` WHERE user_id=?", (user_id,))

    def add_product(self, manufacturer, taste, puffs, amount):
        with self.connection:
            check = self.cursor.execute(
                "SELECT DISTINCT 1 FROM `products` WHERE `manufacturer`=? AND `taste`=? AND `number_of_puffs`=? AND `amount`=?", (manufacturer, taste, puffs, amount)).fetchone()
            if check == None:
                return self.cursor.execute("INSERT INTO `products` (`manufacturer`, `taste`, `number_of_puffs`, `amount`) VALUES(?,?,?,?) ", (manufacturer, taste, puffs, amount))
            else:
                return False

    def get_product_id(self, manufacturer, taste, puffs):
        with self.connection:
            self.cursor.execute(
                "SELECT id FROM products WHERE `manufacturer`=? AND `taste`=? AND `number_of_puffs`=?", (manufacturer, taste, puffs))
            return self.cursor.fetchone()

    def add_product_to_shopping_cart(self, user_id, product_id, count):
        with self.connection:
            check = self.cursor.execute(
                "SELECT DISTINCT 1 FROM `shopping_cart` WHERE `user_id`=? AND `product_id`=?", (user_id, product_id)).fetchone()
            if check == None:
                return self.cursor.execute("INSERT INTO `shopping_cart` (`user_id`, `product_id`, `count`) VALUES(?,?,?) ", (user_id, product_id, count))
            else:
                count_old = (self.cursor.execute(
                    "SELECT count FROM `shopping_cart` WHERE user_id=? AND product_id=?", (user_id, product_id)).fetchone())[0]
                count_new = count_old + count
                return self.cursor.execute("UPDATE `shopping_cart` SET `count`=? WHERE user_id=? AND product_id=?", (count_new, user_id, product_id))

    def get_manufacturers(self):
        with self.connection:
            self.cursor.execute(
                "SELECT manufacturer FROM products")
            return self.cursor.fetchall()

    def get_tastes(self, manufacturer):
        with self.connection:
            self.cursor.execute(
                "SELECT taste FROM products WHERE manufacturer=?", (manufacturer,))
            return self.cursor.fetchall()

    def get_puffs_and_amount(self, manufacturer, taste):
        with self.connection:
            self.cursor.execute(
                "SELECT number_of_puffs, amount FROM products WHERE manufacturer=? AND taste=?", (manufacturer, taste))
            return self.cursor.fetchall()

    def get_orders(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT product_id, count FROM shopping_cart WHERE user_id=?", (user_id,))
            return self.cursor.fetchall()

    def get_amount(self, product_id):
        with self.connection:
            self.cursor.execute(
                "SELECT amount FROM products WHERE id=?", (product_id,))
            return self.cursor.fetchone()

    def delete_product_from_shopping_cart(self, user_id, product_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `shopping_cart` WHERE user_id=? AND product_id=?", (user_id, product_id))

    def delete_product_from_shopping_cart_everyone_has(self, product_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `shopping_cart` WHERE product_id=?", (product_id,))

    def clear_shopping_cart_for_user(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `shopping_cart` WHERE user_id=?", (user_id,))

    def delete_product(self, product_id):
        with self.connection:
            check = self.cursor.execute(
                "SELECT DISTINCT 1 FROM `products` WHERE id=?", (product_id,)).fetchone()
            if check != None:
                return self.cursor.execute(
                    "DELETE FROM `products` WHERE id=?", (product_id,))
            else:
                return False

    def get_product_by_product_id(self, product_id):
        with self.connection:
            self.cursor.execute(
                "SELECT manufacturer, taste, number_of_puffs, amount FROM products WHERE id=?", (product_id,))
            return self.cursor.fetchone()

    def add_name_to_castomer(self, user_id, name):
        with self.connection:
            return self.cursor.execute("INSERT INTO `castomers` (`user_id`, `name`) VALUES(?,?) ", (user_id, name))

    def add_phone_to_castomer(self, user_id, phone):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `castomers` SET `phone_number`=? WHERE user_id=?", (phone, user_id))

    def add_address_to_castomer(self, user_id, address):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `castomers` SET `address`=? WHERE user_id=?", (address, user_id))

    def add_delivery_time_to_castomer(self, user_id, delivery_time):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `castomers` SET `delivery_time`=? WHERE user_id=?", (delivery_time, user_id))

    def add_payment_method_to_castomer(self, user_id, payment_method):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `castomers` SET `payment_method`=? WHERE user_id=?", (payment_method, user_id))

    def get_castomer(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT * FROM castomers WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()

    def delete_castomer(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `castomers` WHERE user_id=?", (user_id,))

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
