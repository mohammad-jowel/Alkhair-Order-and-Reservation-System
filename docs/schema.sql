-- ========================================================
-- Schema DDL for Alkhair Order and Reservation System
-- Target: MySQL 8.0+
-- Database: project_alkhair
-- Generated for BIK11003 Database Coursework
-- ========================================================

SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for table `account`
DROP TABLE IF EXISTS `account`;
CREATE TABLE `account` (
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `account_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `menu_category`
DROP TABLE IF EXISTS `menu_category`;
CREATE TABLE `menu_category` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `category_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `menu_item`
DROP TABLE IF EXISTS `menu_item`;
CREATE TABLE `menu_item` (
  `item_id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `image` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_available` tinyint(1) NOT NULL,
  `category_id` int NOT NULL,
  PRIMARY KEY (`item_id`),
  KEY `menu_item_categor_ab58f2_idx` (`category_id`),
  CONSTRAINT `menu_item_category_id_685695be_fk_menu_category_category_id` FOREIGN KEY (`category_id`) REFERENCES `menu_category` (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `restaurant_table`
DROP TABLE IF EXISTS `restaurant_table`;
CREATE TABLE `restaurant_table` (
  `table_id` int NOT NULL AUTO_INCREMENT,
  `table_number` int NOT NULL,
  `qr_token` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`table_id`),
  UNIQUE KEY `table_number` (`table_number`),
  UNIQUE KEY `qr_token` (`qr_token`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `orders`
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `order_id` int NOT NULL AUTO_INCREMENT,
  `order_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `delivery_address` longtext COLLATE utf8mb4_unicode_ci,
  `order_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `order_date` datetime(6) NOT NULL,
  `account_id` int NOT NULL,
  `table_id` int DEFAULT NULL,
  PRIMARY KEY (`order_id`),
  KEY `orders_account_4fe38e_idx` (`account_id`),
  KEY `orders_table_i_50e4d9_idx` (`table_id`),
  KEY `orders_order_d_6e39a9_idx` (`order_date`),
  KEY `orders_order_date_20533752` (`order_date`),
  CONSTRAINT `orders_account_id_92f83327_fk_account_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`),
  CONSTRAINT `orders_table_id_15dfbe0a_fk_restaurant_table_table_id` FOREIGN KEY (`table_id`) REFERENCES `restaurant_table` (`table_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `order_item`
DROP TABLE IF EXISTS `order_item`;
CREATE TABLE `order_item` (
  `order_item_id` int NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `item_id` int NOT NULL,
  `order_id` int NOT NULL,
  PRIMARY KEY (`order_item_id`),
  UNIQUE KEY `unique_order_item` (`order_id`,`item_id`),
  KEY `order_item_order_i_08a5da_idx` (`order_id`),
  KEY `order_item_item_id_c4c447_idx` (`item_id`),
  CONSTRAINT `order_item_item_id_00cc36f1_fk_menu_item_item_id` FOREIGN KEY (`item_id`) REFERENCES `menu_item` (`item_id`),
  CONSTRAINT `order_item_order_id_0ca9e92e_fk_orders_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
  CONSTRAINT `order_item_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for table `reservation`
DROP TABLE IF EXISTS `reservation`;
CREATE TABLE `reservation` (
  `reservation_id` int NOT NULL AUTO_INCREMENT,
  `reservation_date` date NOT NULL,
  `reservation_time` time(6) NOT NULL,
  `party_size` int unsigned NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `note` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `account_id` int NOT NULL,
  PRIMARY KEY (`reservation_id`),
  KEY `reservation_account_f4fd56_idx` (`account_id`),
  KEY `reservation_reserva_5bf209_idx` (`reservation_date`),
  CONSTRAINT `reservation_account_id_e055fd15_fk_account_account_id` FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`),
  CONSTRAINT `reservation_chk_1` CHECK ((`party_size` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
