docker run -p 3306:3306 -v zesje_db_dev:/var/lib/mysql -e MYSQL_DATABASE=course -e MYSQL_ROOT_PASSWORD=zesje -e MYSQL_ROOT_HOST=172.17.0.1 --name=zesje-mysql-dev -d mysql/mysql-server:5.7
