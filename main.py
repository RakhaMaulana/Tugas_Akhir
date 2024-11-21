import BlindSig as bs
import hashlib
import random
import cryptomath
import sqlite3

class poll:
    def __init__(self):
        self.signer = bs.Signer()
        self.publicKey = self.signer.getPublicKey()
        self.privateKey = self.signer.privateKey
        self.n = self.publicKey['n']
        self.e = self.publicKey['e']

    def get_db_connection(self):
        """Create a new database connection."""
        conn = sqlite3.connect('voting.db')
        return conn

    def is_valid_voter(self, id_number):
        """Memeriksa apakah ID terdaftar dan belum memberikan suara"""
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute('SELECT has_voted, status FROM voters WHERE id_number = ?', (id_number,))
        result = c.fetchone()
        conn.close()
        if result is None:
            print("ID number tidak terdaftar.")
            return False
        elif result[1] != 'approved':
            print("ID number belum disetujui.")
            return False
        elif result[0]:
            print("ID number sudah melakukan voting.")
            return False
        return True

    def mark_voter(self, id_number):
        """Menandai ID sebagai telah memberikan suara"""
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE voters SET has_voted = 1 WHERE id_number = ?', (id_number,))
        conn.commit()
        conn.close()

    def poll_response(self, poll_answer, id_number):
        # Validasi ID number
        if not self.is_valid_voter(id_number):
            return "ID number tidak valid atau sudah digunakan untuk voting."

        # Jika ID valid, lanjutkan dengan proses voting
        print('\n\n')
        for i in range(100):
            print("-", end="")
        print()
        for i in range(50):
            print(" ", end="")
        print("\u001b[31mMODULE 2\u001b[37m")
        for i in range(100):
            print("-", end="")
        print('\n\n')
        print("\u001b[32;1m2. Voter Prepares Ballot for getting signed by Signing Authority:\u001b[0m", end='\n\n')
        print()
        print("\u001b[35;1m(a) Generates random x such that 1<=x<=n\u001b[0m", end='\n\n')
        x = random.randint(1, self.n)
        print("\u001b[33;1mx: \u001b[0m", x, end="\n\n")

        print("\u001b[35;1m(b) Voter chooses favorite candidate, option, etc. on ballot\u001b[0m", end='\n\n')
        message = poll_answer
        print("\u001b[33;1mpoll_answer: \u001b[0m", poll_answer, end="\n\n")
        print("\u001b[35;1m(c) Creates (concatenating) message: poll_answer + x and produces its hash\u001b[0m", end='\n\n')
        concat_message = str(message) + str(x)
        print("\u001b[33;1mConcatenated message: \u001b[0m", concat_message, end="\n\n")
        message_hash = hashlib.sha256(concat_message.encode('utf-8')).hexdigest()
        message_hash = int(message_hash, 16)
        print("\u001b[33;1mhash(concatenated_message), m= \u001b[0m", message_hash, end="\n\n")
        voter = bs.Voter(self.n, id_number)

        blindMessage = voter.blindMessage(message_hash, self.n, self.e)
        if id_number == 1:
            print("\u001b[33;1mBlinded message: \u001b[0m" + str(blindMessage))
        print()

        print("\u001b[35;1m(f) Sends m'(blinded message) to signing authority\u001b[0m")
        eligible = "y" if self.is_valid_voter(id_number) else "n"
        print(f"Eligibility status: {eligible}")
        signedBlindMessage = self.signer.signMessage(blindMessage, eligible)

        if signedBlindMessage is None:
            print("\u001b[31;1mINELIGIBLE VOTER....VOTE NOT AUTHORIZED!\u001b[0m")
        else:
            print("\u001b[33;1mSigned blinded message: \u001b[0m" + str(signedBlindMessage))
            print()
            signedMessage = voter.unwrapSignature(signedBlindMessage, self.n)

            print('\n\n')
            for i in range(100):
                print("-", end="")
            print()
            for i in range(50):
                print(" ", end="")

            print("\u001b[31mMODULE 5\u001b[37m")
            for i in range(100):
                print("-", end="")
            print('\n\n')

            print("\u001b[32;1m5. Ballot Received and it's Verification \u001b[0m", end='\n\n')
            print("\u001b[35;1mA voter's vote in the ballot shall consist of the following: \u001b[0m", end='\n\n')
            print("\u001b[33;1m(a) His vote concatened with a number x: \u001b[0m", concat_message)
            print()
            print("\u001b[33;1m(b) The hash of his concatenated vote signed by authority which is basically the hashed message encrypted with signing authority's private key (m^d) mod n : \u001b[0m", signedMessage)
            print()
            verificationStatus, decoded_message = bs.verifySignature(message, x, signedMessage, self.e, self.n)

            print()
            print("\u001b[33;1mVerification status: \u001b[0m" + str(verificationStatus), end="\n\n")
            if verificationStatus:
                print("\u001b[35;1mSince the verification is true, Hence the vote is the first digit of the concatenated message: \u001b[0m", decoded_message, end='\n\n\n\n')

                # Save to database
                self.save_vote(blinded_message=blindMessage, signed_blinded_message=signedBlindMessage, signed_message=signedMessage, n=self.n, e=self.e, message_hash=message_hash, concatenated_message=concat_message)

                # Tandai ID sebagai telah memberikan suara
                self.mark_voter(id_number)

    def save_vote(self, blinded_message, signed_blinded_message, signed_message, n, e, message_hash, concatenated_message):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO votes (blinded_message, signed_blinded_message, signed_message, n, e, message_hash, concatenated_message) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (str(blinded_message), str(signed_blinded_message), str(signed_message), str(n), str(e), str(message_hash), concatenated_message))
        conn.commit()
        conn.close()

class poll_machine:
    def __init__(self):
        self.p = poll()

    def start_poll(self, poll_answer, id_number):
        self.p.poll_response(poll_answer, id_number)

pm = poll_machine()