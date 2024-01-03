import tkinter as tk
from tkinter import filedialog, Text, Listbox, Toplevel
import threading
import requests
import schedule
import time
import json

from whatsapp_chatbot_python import GreenAPIBot, Notification

bot = GreenAPIBot(
    "7103890538", "b3c8b6f025984b06859768b6da7d027b6dc03c37754f43fc91"
)

API_TOKEN = "b3c8b6f025984b06859768b6da7d027b6dc03c37754f43fc91"

def call_my_api(message):
    response = requests.post('http://54.169.239.63:8501/predict', json={'query_text': message})
    return response.json().get('answer', 'Sorry, I could not process your request.')

@bot.router.message()
def message_handler(notification: Notification):
    try:
        if hasattr(notification, 'text'):
            incoming_message = notification.text
        elif hasattr(notification, 'message_text'):
            incoming_message = notification.message_text
        elif hasattr(notification, 'body') and hasattr(notification.body, 'text'):
            incoming_message = notification.body.text
        else:
            raise AttributeError("Unable to find message text in the notification object")

        api_response = call_my_api(incoming_message)
        notification.answer(api_response)

    except Exception as e:
        print(f"An error occurred: {e}")

def send_message(chat_id, message):
    api_url = f"https://api.green-api.com/waInstance7103890538/sendMessage/b3c8b6f025984b06859768b6da7d027b6dc03c37754f43fc91"
    payload = json.dumps({"chatId": chat_id, "message": message})
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.post(api_url, headers=headers, data=payload)
    print(response.text.encode('utf8'))

def send_file(chat_id, file_path, file_caption, file_type):
    url = f"https://api.green-api.com/waInstance7103890538/sendFileByUpload/b3c8b6f025984b06859768b6da7d027b6dc03c37754f43fc91"
    payload = {'chatId': chat_id, 'caption': file_caption}
    files = [('file', (file_path, open(file_path, 'rb'), file_type))]
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.post(url, headers=headers, data=payload, files=files)
    print(response.text.encode('utf8'))

def set_custom_reminder(time_str, message):
    schedule.every().day.at(time_str).do(lambda: send_message("84379760352@c.us", message))

def get_contacts():
    api_url = f"https://api.green-api.com/waInstance7103890538/getContacts/b3c8b6f025984b06859768b6da7d027b6dc03c37754f43fc91"
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.get(api_url, headers=headers)
    contacts = response.json() if response.status_code == 200 else []
    print("Contacts:", contacts)  # Debug print
    return contacts

def get_chat_history(contact_id, max_messages=5):
    api_url = f"https://api.green-api.com/waInstance7103890538/getChatHistory/b3c8b6f025984b06859768b6da7d027b6dc03c37754f43fc91"
    payload = {
        "chatId": contact_id,
        "count": max_messages
    }
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        chat_history = response.json()
        # Parse messages based on their type (outgoing or incoming)
        formatted_history = []
        for msg in chat_history:
            if msg['type'] == 'outgoing':
                formatted_history.append(msg.get('textMessage', 'No message text found'))
            elif msg['type'] == 'incoming':
                formatted_history.append(msg.get('textMessage', 'No message text found'))
        return formatted_history
    else:
        error_msg = f"Failed to get chat history: {response.status_code}, {response.text}"
        print(error_msg)
        return [error_msg]
    
def filter_active_contacts():
    active_contacts = []
    contacts = get_contacts()
    for contact in contacts:
        chat_history = get_chat_history(contact['id'])
        if chat_history:
            active_contacts.append(contact['id'])
    return active_contacts

def launch_gui():
    def update_chat_listbox(contacts):
        chat_listbox.delete(0, tk.END)
        if contacts:
            for contact in contacts:
                contact_id = contact.get('id', 'No ID Found')
                chat_listbox.insert(tk.END, contact_id)
        else:
            chat_listbox.insert(tk.END, "No contacts found.")

    def on_refresh_chats():
        contacts = get_contacts()
        update_chat_listbox(contacts)

    def on_set_reminder():
        reminder_time = time_entry.get()
        reminder_message = message_entry.get()
        set_custom_reminder(reminder_time, reminder_message)

    def on_select_audio_file():
        filename = filedialog.askopenfilename(title="Select an Audio File", filetypes=[("Audio Files", "*.mp3;*.ogg")])
        if filename:
            send_file("84379760352@c.us", filename, "Audio file", "audio/ogg")

    def on_select_video_file():
        filename = filedialog.askopenfilename(title="Select a Video File", filetypes=[("Video Files", "*.mp4")])
        if filename:
            send_file("84379760352@c.us", filename, "Video file", "video/mp4")

    def update_chat_display():
            contacts = get_contacts()
            chat_listbox.delete(0, tk.END)
            if contacts:
                for contact in contacts:
                    contact_id = contact.get('id', 'No ID Found')
                    chat_listbox.insert(tk.END, contact_id)
            else:
                chat_listbox.insert(tk.END, "No contacts found.")

    def show_chat_history(event):
        print("Attempting to show chat history...")  # Debug print
        selection = chat_listbox.curselection()
        if selection:
            selected_contact = chat_listbox.get(selection[0])
            print(f"Selected contact: {selected_contact}")  # Debug print
            chat_history = get_chat_history(selected_contact)
            print(f"Chat history received: {chat_history}")  # Debug print
            history_window = Toplevel(root)
            history_window.title(f"Chat History with {selected_contact}")
            history_text = Text(history_window, wrap='word')
            history_text.pack(expand=True, fill='both')
            for message in chat_history:
                history_text.insert(tk.END, f"{message}\n")

    root = tk.Tk()
    root.title("WhatsApp Bot Scheduler")

    tk.Label(root, text="Reminder Time (HH:MM):").grid(row=0, column=0)
    time_entry = tk.Entry(root)
    time_entry.grid(row=0, column=1)

    tk.Label(root, text="Reminder Message:").grid(row=1, column=0)
    message_entry = tk.Entry(root)
    message_entry.grid(row=1, column=1)

    tk.Button(root, text="Set Reminder", command=on_set_reminder).grid(row=2, column=1)
    tk.Button(root, text="Select Audio File", command=on_select_audio_file).grid(row=3, column=0)
    tk.Button(root, text="Select Video File", command=on_select_video_file).grid(row=3, column=1)

    chat_listbox = Listbox(root)
    chat_listbox.grid(row=4, column=0, columnspan=2, sticky="ew")
    chat_listbox.bind('<<ListboxSelect>>', show_chat_history)

    tk.Button(root, text="Refresh Chats", command=on_refresh_chats).grid(row=5, column=1)

    # Initialize chat listbox with contacts
    on_refresh_chats()

    root.mainloop()

gui_thread = threading.Thread(target=launch_gui, daemon=True)
gui_thread.start()

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

bot.run_forever()