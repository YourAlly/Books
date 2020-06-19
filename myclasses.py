class Review:
    def __init__(self, user, text, score, user_id):
        self.user_id = user_id
        self.user = user 
        self.text = text
        self.user_score = score