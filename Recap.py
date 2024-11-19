import sqlite3
import hashlib

class Recapitulation:
    def __init__(self):
        pass

    def recapitulate_votes(self):
        conn = sqlite3.connect('voting.db')
        c = conn.cursor()
        c.execute("SELECT * FROM votes")
        votes = c.fetchall()
        conn.close()

        vote_counts = {}
        for vote in votes:
            blinded_message, signed_blinded_message, signed_message, n, e, message_hash, concatenated_message = vote
            signed_message = int(signed_message)
            n = int(n)
            e = int(e)
            message_hash = int(message_hash)

            # Decrypt signed_message using public key
            decrypted_message = pow(signed_message, e, n)

            # Verify the decrypted result with the original hash
            if decrypted_message == message_hash:
                original_vote = concatenated_message[0]  # Assuming the first character is the original vote
                if original_vote in vote_counts:
                    vote_counts[original_vote] += 1
                else:
                    vote_counts[original_vote] = 1

        print(f"{'Vote':<10} {'Count':<10}")
        print("="*20)
        for vote, count in vote_counts.items():
            print(f"{vote:<10} {count:<10}")

recap = Recapitulation()
recap.recapitulate_votes()