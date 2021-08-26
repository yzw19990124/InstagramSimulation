CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP Table IF EXISTS Albums CASCADE;
DROP Table IF Exists FriendRequest CASCADE; 

CREATE TABLE Users(
    user_id int4 AUTO_INCREMENT,
    first_name VARCHAR(20), 
    last_name VARCHAR(20), 
    email varchar(50) UNIQUE,
    birth_date DATE, 
    hometown VARCHAR(20), 
    gender VARCHAR(10), 
    password varchar(30) NOT NULL,
	PRIMARY KEY (user_id)
);


CREATE TABLE Albums(
	album_id int4 AUTO_INCREMENT,
	album_name VARCHAR(50) NOT NULL,
	date DATE,
	user_id INTEGER NOT NULL,
	PRIMARY KEY (album_id),
	FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Pictures(
	picture_id int4 AUTO_INCREMENT,
    album_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL,
	num_like INTEGER DEFAULT 0,
	imgdata longblob,
	caption VARCHAR(255),
	PRIMARY KEY (picture_id), 
	FOREIGN KEY (user_id) REFERENCES Users(user_id), 
    FOREIGN KEY (album_id) REFERENCES Albums(album_id)
);

CREATE TABLE Comments(
	comment_id int4 AUTO_INCREMENT,
    picture_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL,
	comment_text VARCHAR(100),
	comment_date DATE,
	PRIMARY KEY (comment_id), 
	FOREIGN KEY (user_id) REFERENCES Users(user_id), 
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Likes(
picture_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
PRIMARY KEY (picture_id,user_id),
FOREIGN KEY (user_id) REFERENCES Users(user_id), 
FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Friends(
	user_id1 INTEGER NOT NULL,
	user_id2 INTEGER NOT NULL,
	PRIMARY KEY (user_id1, user_id2),
	FOREIGN KEY (user_id1) REFERENCES Users(user_id),
	FOREIGN KEY (user_id2) REFERENCES Users(user_id)
);

CREATE TABLE FriendRequest(
	sender_id INTEGER NOT NULL, 
    recipient_id INTEGER NOT NULL, 
    message VARCHAR(150), 
    PRIMARY KEY(sender_id, recipient_id), 
	FOREIGN KEY (sender_id) REFERENCES Users(user_id),
	FOREIGN KEY (recipient_id) REFERENCES Users(user_id)
); 

CREATE TABLE Tags(
	tag_id int4 AUTO_INCREMENT,
    picture_id INTEGER NOT NULL,
    tag VARCHAR(50),
    PRIMARY KEY (tag_id),
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
    );

INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password) 
VALUES ('bob', 'W', 'test1@bu.edu', '2008-11-12', 'MA', 'male', 'test');

INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password) 
VALUES ('Kate', 'J', 'test2@bu.edu', '2008-11-03', 'MA', 'female', 'test');

INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password) 
VALUES ('Tim', 'Y', 'test3@bu.edu', '2009-11-22', 'MA', 'male', 'test');