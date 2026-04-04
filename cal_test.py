import tkinter as tk
import random


class StressTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("压力心算测试")
        self.root.geometry("800x600")

        self.grade_choice = None
        self.problems = []
        self.current_problem = 0
        self.answered = False
        self.after_id = None
        self.started = False
        self.problem_answers = []
        self.result_shown = False  # 新增变量，用于标记结果是否已经显示

        self.choice_label = tk.Label(
            root,
            text="请选择测试档次：\n1. 小学档（50道加减法）\n2. 中学档（50道加减乘除混搭）",
            font=("Arial", 24),
            wraplength=700
        )
        self.choice_label.pack(pady=100)

        self.root.bind("<Key>", self.handle_choice)

    def handle_choice(self, event):
        try:
            choice = int(event.char)
            if choice == 1:
                self.grade_choice = "小学档"
                self.problems = self.generate_primary_problems(50)
            elif choice == 2:
                self.grade_choice = "中学档"
                self.problems = self.generate_middle_problems(50)
            else:
                return

            self.choice_label.pack_forget()
            self.start_test()
        except ValueError:
            pass

    def generate_primary_problems(self, num):
        problems = []
        for _ in range(num):
            a = random.randint(1, 100)
            b = random.randint(1, a)  # 保证减法结果非负
            operator = random.choice(['+', '-'])
            if operator == '+':
                correct_result = a + b
            else:
                correct_result = a - b
            if random.choice([True, False]):
                equation = f"{a} {operator} {b} = {correct_result}"
                is_correct = True
            else:
                offset = random.choice([-2, -1, 1, 2])
                wrong_result = correct_result + offset
                equation = f"{a} {operator} {b} = {wrong_result}"
                is_correct = False
            problems.append((equation, is_correct))
        return problems

    def generate_middle_problems(self, num):
        problems = []
        operators = ['+', '-', '*', '/']
        for _ in range(num):
            operator = random.choice(operators)
            if operator == '+':
                a = random.randint(1, 100)
                b = random.randint(1, 100)
            elif operator == '*':
                a = random.randint(1, 30)
                b = random.randint(1, 30)
            elif operator == '-':
                a = random.randint(1, 200)
                b = random.randint(1, a)  # 保证减法结果非负
            else:  # 除法
                while True:
                    a = random.randint(2, 200)  # 被除数从 2 开始，保证商大于 1
                    b = random.randint(1, a - 1)  # 除数小于被除数
                    quotient = a // b
                    if a % b == 0 and quotient > 1:
                        break

            if operator == '+':
                correct_result = a + b
            elif operator == '-':
                correct_result = a - b
            elif operator == '*':
                correct_result = a * b
            else:
                correct_result = a // b

            if random.choice([True, False]):
                equation = f"{a} {operator} {b} = {correct_result}"
                is_correct = True
            else:
                offset = random.choice([-2, -1, 1, 2, -3, 3, -13, -12, -11, -10, 10, 11, 12, 13, -20, 20, -21, -22, 21, 22])
                wrong_result = correct_result + offset
                equation = f"{a} {operator} {b} = {wrong_result}"
                is_correct = False
            problems.append((equation, is_correct))
        return problems

    def start_test(self):
        if not self.started:
            self.started = True
            self.introduction_label = tk.Label(
                self.root,
                text=f"你选择了{self.grade_choice}。在本次压力心算测试中，\n请判断屏幕上显示的算式是否正确。\n如果正确，请按 'N' 键；如果错误，请按 'M' 键。\n每题限时 4 秒，超时将显示“超时”。\n按空格开始测试。",
                font=("Arial", 24),
                wraplength=700
            )
            self.introduction_label.pack(pady=100)
            self.root.bind("<space>", self.begin_test)
            self.root.bind("<Key>", self.handle_key)

    def begin_test(self, event=None):
        self.introduction_label.pack_forget()
        self.equation_label = tk.Label(self.root, font=("Arial", 48))
        self.equation_label.pack(pady=100)
        self.feedback_label = tk.Label(self.root, font=("Arial", 24))
        self.feedback_label.pack()
        self.show_problem()

    def show_problem(self):
        self.answered = False
        if self.current_problem >= len(self.problems) and not self.result_shown:
            self.show_result()
            return

        equation, is_correct = self.problems[self.current_problem]
        self.equation_label.config(text=equation)
        self.current_is_correct = is_correct

        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(4000, self.timeout)

    def check_answer(self, event):
        if self.answered:
            return
        self.answered = True

        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        user_key = event.keysym.lower()
        self.problem_answers.append(user_key)
        is_correct_answer = (
                (user_key == "n" and self.current_is_correct) or
                (user_key == "m" and not self.current_is_correct)
        )

        if is_correct_answer:
            self.feedback_label.config(text="正确", fg="green", font=("Arial", 48))
        else:
            self.feedback_label.config(text="错误", fg="red", font=("Arial", 48))

        self.root.after(500, self.next_problem)

    def timeout(self):
        if self.answered:
            return
        self.answered = True
        self.problem_answers.append(None)  # 超时记录为 None
        self.feedback_label.config(text="超时", fg="red", font=("Arial", 48))
        self.root.after(500, self.next_problem)

    def next_problem(self):
        self.current_problem += 1
        self.feedback_label.config(text="")
        self.show_problem()

    def show_result(self):
        correct_count = 0
        for i in range(len(self.problems)):
            _, is_correct = self.problems[i]
            answer = self.problem_answers[i]
            if answer is not None and ((answer == "n" and is_correct) or (answer == "m" and not is_correct)):
                correct_count += 1
        accuracy = correct_count / len(self.problems) * 100
        self.equation_label.pack_forget()
        self.feedback_label.pack_forget()

        self.result_label = tk.Label(self.root, text=f"答题正确率: {accuracy:.2f}%", fg="red", font=("Arial", 48))
        self.result_label.pack(pady=100)
        self.result_shown = True  # 标记结果已显示

    def handle_key(self, event):
        if not self.answered and not self.result_shown:
            if event.keysym.lower() in ['n', 'm']:
                self.check_answer(event)


if __name__ == "__main__":
    root = tk.Tk()
    app = StressTestApp(root)
    root.mainloop()