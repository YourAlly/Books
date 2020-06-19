class Review:
    def __init__(self, user_id, user, book_isbn, score, text):
        self.user_id = user_id
        self.user = user
        self.book_isbn = book_isbn
        self.user_score = score
        self.user_review = text
