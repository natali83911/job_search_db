from src.utils import user_interface_with_keyword, setup_and_fill_database

if __name__ == "__main__":
    db_manager = setup_and_fill_database("hh_db")
    user_interface_with_keyword(db_manager)
