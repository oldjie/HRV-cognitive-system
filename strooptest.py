import tkinter as tk
import random

class StroopTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stroop 测试")
        self.root.geometry("800x600")

        self.color_words = ["红", "绿", "蓝", "黄", "紫", "黑"]
        self.color_map = {
            "红": "red",
            "绿": "green",
            "蓝": "blue",
            "黄": "yellow",
            "紫": "purple",
            "黑": "black"
        }

        # 用于存储随机生成的题目列表
        self.problems = []
        self.current_problem_idx = 0

        # 标识当前题是否已回答或已超时
        self.answered = False
        self.after_id = None

        # 测试是否已经启动
        self.started = False
        # 是否已经显示了自评环节
        self.self_assessment_shown = False

        # 介绍说明 Label
        self.introduction_label = tk.Label(
            root,
            text=(
                "欢迎进入中文版本的 Stroop 测试！\n\n"
                "程序会随机显示一个颜色词（如“红”），并以某种字体颜色呈现。\n"
                "如果颜色词含义与其字体颜色一致（例如“红”用红色字体），请按 'N' 键。\n"
                "如果颜色词含义与其字体颜色不一致（例如“红”用绿色字体），请按 'M' 键。\n"
                "每题限时 4 秒，超时将自动显示“超时”。\n\n"
                "完成所有题目后，会要求您进行 1 - 5 的焦虑/压力自评。\n\n"
                "按空格键开始测试。"
            ),
            font=("Arial", 20),
            wraplength=700,
            justify="left"
        )
        self.introduction_label.pack(pady=50)

        # 绑定空格键以启动测试
        self.root.bind("<space>", self.start_test)

    def start_test(self, event=None):
        if not self.started:
            self.started = True
            self.introduction_label.pack_forget()

            # 生成测试题目
            self.generate_problems(num=20)

            # 显示题目的 Label
            self.word_label = tk.Label(self.root, font=("Arial", 48))
            self.word_label.pack(pady=50)

            # 反馈 Label
            self.feedback_label = tk.Label(self.root, font=("Arial", 36))
            self.feedback_label.pack(pady=20)

            # 绑定按键，用于答题：N/M
            self.root.bind("<Key>", self.handle_key)

            # 显示第一题
            self.show_problem()

    def generate_problems(self, num=20):

        self.problems = []
        for _ in range(num):
            word = random.choice(self.color_words)
            color_name = random.choice(self.color_words)
            is_correct = (word == color_name)  # True 表示文字与颜色含义一致

            self.problems.append(
                (word, self.color_map[color_name], is_correct)
            )

        random.shuffle(self.problems)

    def show_problem(self):

        self.answered = False

        if self.current_problem_idx >= len(self.problems):
            self.show_self_assessment()
            return

        word, font_color, is_correct = self.problems[self.current_problem_idx]
        # 设置 Label 显示内容
        self.word_label.config(text=word, fg=font_color)
        self.feedback_label.config(text="")

        # 每题限时 4 秒
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(4000, self.timeout)

    def handle_key(self, event):
        # 如果已经进入自评阶段，则处理自评输入
        if self.self_assessment_shown:
            self.handle_self_assessment_input(event)
            return

        # 如果当前题已回答或超时，不再处理输入
        if self.answered:
            return

        user_key = event.keysym.lower()
        if user_key not in ["n", "m"]:
            return

        self.answered = True
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        _, _, is_correct = self.problems[self.current_problem_idx]
        # 'N' 表示用户判断一致，'M' 表示不一致
        user_judgement = (user_key == "n")

        if user_judgement == is_correct:
            self.feedback_label.config(text="正确", fg="green")
        else:
            self.feedback_label.config(text="错误", fg="red")

        self.root.after(500, self.next_problem)

    def timeout(self):
        # 超时处理
        if self.answered:
            return
        self.answered = True
        self.feedback_label.config(text="超时", fg="red")
        self.root.after(500, self.next_problem)

    def next_problem(self):
        # 进入下一题
        self.current_problem_idx += 1
        self.show_problem()

    def show_self_assessment(self):
        # 显示自评环节
        self.self_assessment_shown = True
        self.word_label.pack_forget()
        self.feedback_label.pack_forget()

        self.assessment_label = tk.Label(
            self.root,
            text="测试结束！\n\n请输入 1 - 5 的数字进行焦虑/压力等级自评：",
            font=("Arial", 24)
        )
        self.assessment_label.pack(pady=50)

        self.assessment_result_label = tk.Label(self.root, font=("Arial", 24))
        self.assessment_result_label.pack(pady=20)

    def handle_self_assessment_input(self, event):

        try:
            level = int(event.char)
            if 1 <= level <= 5:
                self.assessment_result_label.config(
                    text=f"焦虑/压力等级已记录：{level} 级"
                )
        except ValueError:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = StroopTestApp(root)
    root.mainloop()
