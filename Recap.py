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

        print(f"{'ID':<5} {'Vote':<10} {'Verification Status':<20}")
        print("="*60)

        for vote in votes:
            id, blinded_message, signed_blinded_message, signed_message, n, e, message_hash, concatenated_message = vote
            signed_message = int(signed_message)
            n = int(n)
            e = int(e)
            message_hash = int(message_hash)

            # Dekripsi signed_message menggunakan public key
            decrypted_message = pow(signed_message, e, n)

            # Verifikasi hasil dekripsi dengan hash asli
            if decrypted_message == message_hash:
                verification_status = "Verified"
                original_vote = concatenated_message[0]  # Asumsi digit pertama adalah vote asli
            else:
                verification_status = "Not Verified"
                original_vote = "N/A"

            print(f"{id:<5} {original_vote:<10} {verification_status:<20}")

recap = Recapitulation()
recap.recapitulate_votes()