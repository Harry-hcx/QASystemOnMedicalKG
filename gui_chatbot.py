import tkinter as tk
from tkinter import scrolledtext, messagebox
from question_classifier import *
from question_parser import *
from answer_search import *


class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()

    def chat_main(self, sent):
        answer = "您好，我是小勇医药智能助理，希望可以帮到您。如果没答上来，可联系https://liuhuanyong.github.io/。祝您身体棒棒！"
        res_classify = self.classifier.classify(sent)
        if not res_classify:
            return answer
        res_sql = self.parser.parser_main(res_classify)
        final_answers = self.searcher.search_main(res_sql)
        if not final_answers:
            return answer
        else:
            return "\n".join(final_answers)


class MedicalChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("医药智能助理")
        self.root.geometry("600x500")
        self.chatbot = ChatBotGraph()

        # 创建登录界面
        self.create_login_frame()

    def create_login_frame(self):
        self.login_frame = tk.Frame(self.root)

        tk.Label(self.login_frame, text="用户名:").grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.E
        )
        self.username = tk.Entry(self.login_frame, width=30)
        self.username.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.login_frame, text="密码:").grid(
            row=1, column=0, padx=10, pady=10, sticky=tk.E
        )
        self.password = tk.Entry(self.login_frame, show="*", width=30)
        self.password.grid(row=1, column=1, padx=10, pady=10)

        login_btn = tk.Button(self.login_frame, text="登录", command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)

        self.login_frame.pack(expand=True)

    def login(self):
        # 假登录，不验证用户名密码
        username = self.username.get()
        if not username:
            username = "用户"

        self.login_frame.destroy()
        self.create_chat_frame(username)

    def create_chat_frame(self, username):
        self.chat_frame = tk.Frame(self.root)

        # 聊天历史区域
        self.chat_history = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, width=70, height=20
        )
        self.chat_history.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.chat_history.config(state=tk.DISABLED)

        # 输入区域
        tk.Label(self.chat_frame, text="请输入问题:").grid(
            row=1, column=0, padx=10, sticky=tk.W
        )
        self.question_entry = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, width=50, height=3
        )
        self.question_entry.grid(row=1, column=1, padx=10, pady=10)

        # 发送按钮
        send_btn = tk.Button(self.chat_frame, text="发送", command=self.send_question)
        send_btn.grid(row=2, column=0, columnspan=2, pady=10)

        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        self.add_message("小勇", "您好，我是小勇医药智能助理，希望可以帮到您！")

    def add_message(self, sender, message):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    def send_question(self):
        question = self.question_entry.get("1.0", tk.END).strip()
        if not question:
            return

        # 添加用户问题到聊天记录
        self.add_message("用户", question)
        # 清空输入框
        self.question_entry.delete("1.0", tk.END)

        # 获取回答并显示
        answer = self.chatbot.chat_main(question)
        self.add_message("小勇", answer)


if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalChatGUI(root)
    root.mainloop()
