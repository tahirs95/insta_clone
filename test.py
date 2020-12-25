import csv
import psycopg2

users_query = """
        SELECT * from users
    """

posts_query = """
        SELECT * from posts
    """

followers_query = """
        SELECT * from followers
    """

topics_query = """
        SELECT * from topics
    """

conn = psycopg2.connect(database="insta", user="postgres", host="localhost", password="postgres")

cur = conn.cursor()
cur.execute(users_query)

with open('dump_data/users.csv', 'w') as f:
    writer = csv.writer(f, delimiter=',')
    for row in cur.fetchall():
        writer.writerow(row)

cur.close()

cur = conn.cursor()
cur.execute(posts_query)

with open('dump_data/posts.csv', 'w') as f:
    writer = csv.writer(f, delimiter=',')
    for row in cur.fetchall():
        writer.writerow(row)

cur.close()

cur = conn.cursor()
cur.execute(followers_query)

with open('dump_data/followers.csv', 'w') as f:
    writer = csv.writer(f, delimiter=',')
    for row in cur.fetchall():
        writer.writerow(row)

cur.close()

cur = conn.cursor()
cur.execute(topics_query)

with open('dump_data/topics.csv', 'w') as f:
    writer = csv.writer(f, delimiter=',')
    for row in cur.fetchall():
        writer.writerow(row)

cur.close()

conn.close()