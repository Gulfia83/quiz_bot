def parse_file(file):
    with open(file, "r", encoding='KOI8-R') as my_file:
        file_contents = my_file.read()

    questions_descriptions = file_contents.split('\n\n')
    questions = []
    answers = []
    for part in questions_descriptions:
        if 'Вопрос' in part:
            questions.append(part.split(':\n')[1].replace('\n', ' '))
        if 'Ответ' in part:
            answers.append(part.split(':\n')[1])

    return dict(zip(questions, answers))
