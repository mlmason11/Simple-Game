from . import CONN, CURSOR

class User():

    all_usernames = []

    def __init__(self, username, runs=0, fastest_time=None, id=None):
        self.username = username
        self.runs = runs
        self.fastest_time = fastest_time
        self.id = id

    def __repr__(self):
        print(f"id={self.id}, username={self.username}, runs={self.runs}, fastest_time={self.fastest_time}")


    @classmethod
    def create_table(cls):
        sql="""
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        runs INTEGER,
        fastest_time FLOAT
        )
        """

        CURSOR.execute(sql)

    @classmethod
    def drop_table(cls):
        sql="""DROP TABLE users"""
        CURSOR.execute(sql)

    @classmethod
    def query_all(cls):
        sql = """SELECT * FROM users"""
        user_list = CURSOR.execute(sql).fetchall()
        if user_list:
            return [User(id=user[0], username=user[1], runs=user[2], fastest_time=user[3]) for user in user_list]

    @classmethod
    def query_all_usernames(cls):
        sql = """SELECT username FROM users"""
        username_list = CURSOR.execute(sql).fetchall()
        if username_list:
            return username_list

    @classmethod
    def query_by_username(cls, username):
        sql = """SELECT * FROM users WHERE username = ?"""
        user = CURSOR.execute(sql , [username]).fetchone()
        if user:
            return User(id=user[0], username=user[1], runs=user[2], fastest_time=user[3])


    def create(self):
        sql="""INSERT INTO users (username, runs, fastest_time) VALUES (?, ?, ?)"""
        CURSOR.execute(sql, [self.username, self.runs, self.fastest_time])
        CONN.commit()
        self.id = CURSOR.lastrowid
        User.all_usernames.append(self.username)
        return self
    
    def update(self):
        sql="""
        UPDATE users
        SET username = ?, runs = ?, fastest_time = ?
        WHERE id = ?
        """
        CURSOR.execute(sql, [self.username, self.runs, self.fastest_time, self.id])
        CONN.commit()
        return self
    
    def save(self):
        self.update() if self.id else self.create()

    def post_run_update(self, run_time):
        self.runs += 1
        if not self.fastest_time or run_time < self.fastest_time:
            self.fastest_time = run_time
        self.save()
    