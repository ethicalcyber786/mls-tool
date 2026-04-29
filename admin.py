from app import db, User, app

def update_system():
    with app.app_context():
        print("\n" + "="*30)
        print("   MLS ADMIN CONTROL")
        print("="*30)

        name = input("\n[?] Username: ").strip()
        user = User.query.filter_by(username=name).first()

        if not user:
            print("[!] User not found!")
            return

        print(f"\n[i] User: {user.username} | IP: {user.user_ip}")
        print(f"[i] Credits: {user.credits} | Premium: {user.is_premium}")

        print("\n1. ADD Credits\n2. CUT Credits\n3. GIVE Lifetime\n4. REMOVE Lif>
        choice = input("\n[?] Select (1-5): ")

        if choice == "1":
            user.credits += int(input("[+] Amount: "))
        elif choice == "2":
            user.credits -= int(input("[-] Amount: "))
        elif choice == "3":
            user.is_premium = True
        elif choice == "4":
            user.is_premium = False
        else: return

        db.session.commit()
        print("\n[SUCCESS] DATABASE UPDATED! 🦾")                                
if __name__ == "__main__":
    update_system()
