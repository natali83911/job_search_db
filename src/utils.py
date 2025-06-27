from .db_manager import DBManager



def user_interface_with_keyword(db_manager: DBManager) -> None:
    """
    Функция взаимодействия с пользователем.
    Сначала запрашивает ключевое слово для поиска вакансий,
    затем позволяет выполнять остальные действия с фильтрацией по ключевому слову.
    """
    keyword = input("Введите ключевое слово для поиска вакансий: ").strip()
    if not keyword:
        print("Ключевое слово не может быть пустым. Завершение работы.")
        return

    while True:
        print("\nВыберите действие:")
        print("1 - Показать компании и количество вакансий")
        print("2 - Показать все вакансии")
        print("3 - Показать среднюю зарплату по вакансиям")
        print("4 - Показать вакансии с зарплатой выше средней")
        print(f"5 - Показать вакансии с ключевым словом '{keyword}'")
        print("0 - Выход")

        choice = input("Введите номер действия: ").strip()

        if choice == "1":
            print("\nКомпании и количество вакансий:")
            companies = db_manager.get_companies_and_vacancies_count()
            for name, count in companies:
                print(f"- {name}: {count}")

        elif choice == "2":
            print("\nВсе вакансии:")
            vacancies = db_manager.get_all_vacancies()
            for vacancy_str in vacancies:
                print(f"- {vacancy_str}")

        elif choice == "3":
            avg_salary = db_manager.get_avg_salary()
            if avg_salary is not None:
                print(f"\nСредняя зарплата по вакансиям: {avg_salary:.2f}")
            else:
                print("\nСредняя зарплата не рассчитана.")

        elif choice == "4":
            print("\nВакансии с зарплатой выше средней:")
            vacancies = db_manager.get_vacancies_with_higher_salary()
            for vacancy_str in vacancies:
                print(f"- {vacancy_str}")

        elif choice == "5":
            print(f"\nВакансии с ключевым словом '{keyword}':")
            vacancies = db_manager.get_vacancies_with_keyword(keyword)
            if vacancies:
                for vacancy_str in vacancies:
                    print(f"- {vacancy_str}")
            else:
                print("Вакансии не найдены.")

        elif choice == "0":
            print("Выход из программы.")
            break

        else:
            print("Некорректный ввод. Пожалуйста, введите номер действия из списка.")
