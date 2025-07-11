import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import threading
import time

class Task:
    def __init__(self, title: str, description: str = "", category: str = "General", 
                 priority: str = "Medium", due_date: str = "", completed: bool = False):
        self.id = int(time.time() * 1000000)  # Unique ID based on timestamp
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.due_date = due_date
        self.completed = completed
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.completed_at = None
    
    def mark_complete(self):
        self.completed = True
        self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def mark_incomplete(self):
        self.completed = False
        self.completed_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'due_date': self.due_date,
            'completed': self.completed,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        task = cls(
            title=data['title'],
            description=data.get('description', ''),
            category=data.get('category', 'General'),
            priority=data.get('priority', 'Medium'),
            due_date=data.get('due_date', ''),
            completed=data.get('completed', False)
        )
        task.id = data['id']
        task.created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        task.completed_at = data.get('completed_at')
        return task

class AdvancedTaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Task Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Data storage
        self.tasks: List[Task] = []
        self.categories = ["General", "Work", "Personal", "Health", "Education", "Finance"]
        self.priorities = ["Low", "Medium", "High", "Critical"]
        self.data_file = "tasks.json"
        
        # Load existing tasks
        self.load_tasks()
        
        # Create GUI
        self.create_styles()
        self.create_widgets()
        self.refresh_task_list()
        
        # Auto-save every 30 seconds
        self.auto_save_thread = threading.Thread(target=self.auto_save_loop, daemon=True)
        self.auto_save_thread.start()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_styles(self):
        """Create custom styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', 
                       background='#2c3e50', 
                       foreground='#ecf0f1', 
                       font=('Arial', 16, 'bold'))
        
        style.configure('Heading.TLabel', 
                       background='#34495e', 
                       foreground='#ecf0f1', 
                       font=('Arial', 12, 'bold'))
        
        style.configure('Custom.TFrame', background='#34495e')
        style.configure('TaskFrame.TFrame', background='#ecf0f1', relief='raised')
        
        # Treeview styling
        style.configure('Custom.Treeview', 
                       background='#ecf0f1',
                       foreground='#2c3e50',
                       rowheight=25,
                       font=('Arial', 10))
        
        style.configure('Custom.Treeview.Heading',
                       background='#3498db',
                       foreground='white',
                       font=('Arial', 11, 'bold'))
        
        # Button styling
        style.configure('Action.TButton',
                       background='#3498db',
                       foreground='white',
                       font=('Arial', 10, 'bold'),
                       padding=10)
        
        style.configure('Success.TButton',
                       background='#27ae60',
                       foreground='white',
                       font=('Arial', 10, 'bold'),
                       padding=10)
        
        style.configure('Danger.TButton',
                       background='#e74c3c',
                       foreground='white',
                       font=('Arial', 10, 'bold'),
                       padding=10)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main title
        title_label = ttk.Label(self.root, text="📋 Advanced Task Manager", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Main container
        main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left panel - Task input and controls
        left_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # Task input section
        input_frame = ttk.LabelFrame(left_frame, text="Add New Task", 
                                    style='Custom.TFrame')
        input_frame.pack(fill='x', pady=5)
        
        # Task title
        ttk.Label(input_frame, text="Title:", style='Heading.TLabel').pack(anchor='w')
        self.title_entry = ttk.Entry(input_frame, width=30, font=('Arial', 10))
        self.title_entry.pack(fill='x', pady=2)
        
        # Task description
        ttk.Label(input_frame, text="Description:", style='Heading.TLabel').pack(anchor='w')
        self.desc_text = tk.Text(input_frame, height=3, width=30, font=('Arial', 10))
        self.desc_text.pack(fill='x', pady=2)
        
        # Category
        ttk.Label(input_frame, text="Category:", style='Heading.TLabel').pack(anchor='w')
        self.category_combo = ttk.Combobox(input_frame, values=self.categories, 
                                          state='readonly', font=('Arial', 10))
        self.category_combo.set("General")
        self.category_combo.pack(fill='x', pady=2)
        
        # Priority
        ttk.Label(input_frame, text="Priority:", style='Heading.TLabel').pack(anchor='w')
        self.priority_combo = ttk.Combobox(input_frame, values=self.priorities, 
                                          state='readonly', font=('Arial', 10))
        self.priority_combo.set("Medium")
        self.priority_combo.pack(fill='x', pady=2)
        
        # Due date
        ttk.Label(input_frame, text="Due Date (YYYY-MM-DD):", style='Heading.TLabel').pack(anchor='w')
        self.due_date_entry = ttk.Entry(input_frame, width=30, font=('Arial', 10))
        self.due_date_entry.pack(fill='x', pady=2)
        
        # Add task button
        ttk.Button(input_frame, text="➕ Add Task", 
                  command=self.add_task, style='Success.TButton').pack(pady=10)
        
        # Control buttons
        control_frame = ttk.LabelFrame(left_frame, text="Task Controls", 
                                      style='Custom.TFrame')
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="✅ Mark Complete", 
                  command=self.mark_complete, style='Success.TButton').pack(fill='x', pady=2)
        
        ttk.Button(control_frame, text="↩️ Mark Incomplete", 
                  command=self.mark_incomplete, style='Action.TButton').pack(fill='x', pady=2)
        
        ttk.Button(control_frame, text="✏️ Edit Task", 
                  command=self.edit_task, style='Action.TButton').pack(fill='x', pady=2)
        
        ttk.Button(control_frame, text="🗑️ Delete Task", 
                  command=self.delete_task, style='Danger.TButton').pack(fill='x', pady=2)
        
        # Filter section
        filter_frame = ttk.LabelFrame(left_frame, text="Filters", 
                                     style='Custom.TFrame')
        filter_frame.pack(fill='x', pady=5)
        
        # Search
        ttk.Label(filter_frame, text="Search:", style='Heading.TLabel').pack(anchor='w')
        self.search_entry = ttk.Entry(filter_frame, width=30, font=('Arial', 10))
        self.search_entry.pack(fill='x', pady=2)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Filter by category
        ttk.Label(filter_frame, text="Filter by Category:", style='Heading.TLabel').pack(anchor='w')
        self.filter_category = ttk.Combobox(filter_frame, 
                                           values=["All"] + self.categories, 
                                           state='readonly', font=('Arial', 10))
        self.filter_category.set("All")
        self.filter_category.pack(fill='x', pady=2)
        self.filter_category.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Filter by priority
        ttk.Label(filter_frame, text="Filter by Priority:", style='Heading.TLabel').pack(anchor='w')
        self.filter_priority = ttk.Combobox(filter_frame, 
                                           values=["All"] + self.priorities, 
                                           state='readonly', font=('Arial', 10))
        self.filter_priority.set("All")
        self.filter_priority.pack(fill='x', pady=2)
        self.filter_priority.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Filter by status
        ttk.Label(filter_frame, text="Filter by Status:", style='Heading.TLabel').pack(anchor='w')
        self.filter_status = ttk.Combobox(filter_frame, 
                                         values=["All", "Completed", "Pending"], 
                                         state='readonly', font=('Arial', 10))
        self.filter_status.set("All")
        self.filter_status.pack(fill='x', pady=2)
        self.filter_status.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Statistics section
        stats_frame = ttk.LabelFrame(left_frame, text="Statistics", 
                                    style='Custom.TFrame')
        stats_frame.pack(fill='x', pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="", style='Heading.TLabel')
        self.stats_label.pack(pady=5)
        
        # Right panel - Task list
        right_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        right_frame.pack(side='right', fill='both', expand=True)
        
        # Task list
        list_frame = ttk.LabelFrame(right_frame, text="Task List", 
                                   style='Custom.TFrame')
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # Create treeview
        self.tree = ttk.Treeview(list_frame, style='Custom.Treeview', 
                                columns=('Title', 'Category', 'Priority', 'Due Date', 'Status'),
                                show='headings', height=20)
        
        # Define headings
        self.tree.heading('Title', text='Title')
        self.tree.heading('Category', text='Category')
        self.tree.heading('Priority', text='Priority')
        self.tree.heading('Due Date', text='Due Date')
        self.tree.heading('Status', text='Status')
        
        # Define column widths
        self.tree.column('Title', width=200)
        self.tree.column('Category', width=100)
        self.tree.column('Priority', width=80)
        self.tree.column('Due Date', width=100)
        self.tree.column('Status', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to show details
        self.tree.bind('<Double-1>', self.show_task_details)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(right_frame, style='Custom.TFrame')
        bottom_frame.pack(fill='x', pady=5)
        
        ttk.Button(bottom_frame, text="📊 Show Statistics", 
                  command=self.show_detailed_stats, style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(bottom_frame, text="📤 Export Tasks", 
                  command=self.export_tasks, style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(bottom_frame, text="🔄 Refresh", 
                  command=self.refresh_task_list, style='Action.TButton').pack(side='left', padx=5)
    
    def add_task(self):
        """Add a new task"""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "Task title is required!")
            return
        
        description = self.desc_text.get(1.0, tk.END).strip()
        category = self.category_combo.get()
        priority = self.priority_combo.get()
        due_date = self.due_date_entry.get().strip()
        
        # Validate due date format
        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
                return
        
        task = Task(title, description, category, priority, due_date)
        self.tasks.append(task)
        
        # Clear input fields
        self.title_entry.delete(0, tk.END)
        self.desc_text.delete(1.0, tk.END)
        self.category_combo.set("General")
        self.priority_combo.set("Medium")
        self.due_date_entry.delete(0, tk.END)
        
        self.refresh_task_list()
        self.save_tasks()
        messagebox.showinfo("Success", "Task added successfully!")
    
    def get_selected_task(self) -> Optional[Task]:
        """Get the currently selected task"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task first!")
            return None
        
        item = self.tree.item(selection[0])
        task_id = item['values'][0] if item['values'] else None
        
        for task in self.tasks:
            if str(task.id) == str(task_id):
                return task
        
        return None
    
    def mark_complete(self):
        """Mark selected task as complete"""
        task = self.get_selected_task()
        if task:
            task.mark_complete()
            self.refresh_task_list()
            self.save_tasks()
            messagebox.showinfo("Success", "Task marked as complete!")
    
    def mark_incomplete(self):
        """Mark selected task as incomplete"""
        task = self.get_selected_task()
        if task:
            task.mark_incomplete()
            self.refresh_task_list()
            self.save_tasks()
            messagebox.showinfo("Success", "Task marked as incomplete!")
    
    def edit_task(self):
        """Edit selected task"""
        task = self.get_selected_task()
        if not task:
            return
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Task")
        edit_window.geometry("400x500")
        edit_window.configure(bg='#2c3e50')
        edit_window.grab_set()
        
        # Title
        ttk.Label(edit_window, text="Title:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)
        title_entry = ttk.Entry(edit_window, width=40, font=('Arial', 10))
        title_entry.insert(0, task.title)
        title_entry.pack(fill='x', padx=10, pady=2)
        
        # Description
        ttk.Label(edit_window, text="Description:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)
        desc_text = tk.Text(edit_window, height=5, width=40, font=('Arial', 10))
        desc_text.insert(1.0, task.description)
        desc_text.pack(fill='x', padx=10, pady=2)
        
        # Category
        ttk.Label(edit_window, text="Category:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)
        category_combo = ttk.Combobox(edit_window, values=self.categories, state='readonly', font=('Arial', 10))
        category_combo.set(task.category)
        category_combo.pack(fill='x', padx=10, pady=2)
        
        # Priority
        ttk.Label(edit_window, text="Priority:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)
        priority_combo = ttk.Combobox(edit_window, values=self.priorities, state='readonly', font=('Arial', 10))
        priority_combo.set(task.priority)
        priority_combo.pack(fill='x', padx=10, pady=2)
        
        # Due date
        ttk.Label(edit_window, text="Due Date (YYYY-MM-DD):", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)
        due_date_entry = ttk.Entry(edit_window, width=40, font=('Arial', 10))
        due_date_entry.insert(0, task.due_date)
        due_date_entry.pack(fill='x', padx=10, pady=2)
        
        def save_changes():
            new_title = title_entry.get().strip()
            if not new_title:
                messagebox.showerror("Error", "Task title is required!")
                return
            
            new_due_date = due_date_entry.get().strip()
            if new_due_date:
                try:
                    datetime.strptime(new_due_date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
                    return
            
            task.title = new_title
            task.description = desc_text.get(1.0, tk.END).strip()
            task.category = category_combo.get()
            task.priority = priority_combo.get()
            task.due_date = new_due_date
            
            self.refresh_task_list()
            self.save_tasks()
            edit_window.destroy()
            messagebox.showinfo("Success", "Task updated successfully!")
        
        # Buttons
        button_frame = ttk.Frame(edit_window, style='Custom.TFrame')
        button_frame.pack(fill='x', padx=10, pady=20)
        
        ttk.Button(button_frame, text="Save Changes", command=save_changes, 
                  style='Success.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=edit_window.destroy, 
                  style='Danger.TButton').pack(side='right', padx=5)
    
    def delete_task(self):
        """Delete selected task"""
        task = self.get_selected_task()
        if not task:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{task.title}'?"):
            self.tasks.remove(task)
            self.refresh_task_list()
            self.save_tasks()
            messagebox.showinfo("Success", "Task deleted successfully!")
    
    def show_task_details(self, event):
        """Show detailed view of selected task"""
        task = self.get_selected_task()
        if not task:
            return
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Task Details - {task.title}")
        details_window.geometry("500x400")
        details_window.configure(bg='#2c3e50')
        details_window.grab_set()
        
        # Create scrollable text widget
        text_widget = tk.Text(details_window, wrap=tk.WORD, font=('Arial', 12), 
                             bg='#ecf0f1', fg='#2c3e50', padx=20, pady=20)
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Format task details
        details = f"""TASK DETAILS
{'='*50}

Title: {task.title}

Description: {task.description if task.description else 'No description'}

Category: {task.category}

Priority: {task.priority}

Due Date: {task.due_date if task.due_date else 'No due date'}

Status: {'✅ Completed' if task.completed else '⏳ Pending'}

Created: {task.created_at}

{f'Completed: {task.completed_at}' if task.completed_at else ''}

Task ID: {task.id}
"""
        
        text_widget.insert(1.0, details)
        text_widget.config(state='disabled')
    
    def on_search_change(self, event):
        """Handle search input change"""
        self.refresh_task_list()
    
    def on_filter_change(self, event):
        """Handle filter change"""
        self.refresh_task_list()
    
    def get_filtered_tasks(self) -> List[Task]:
        """Get tasks based on current filters"""
        filtered_tasks = self.tasks.copy()
        
        # Search filter
        search_term = self.search_entry.get().lower()
        if search_term:
            filtered_tasks = [task for task in filtered_tasks 
                            if search_term in task.title.lower() or 
                            search_term in task.description.lower()]
        
        # Category filter
        category_filter = self.filter_category.get()
        if category_filter != "All":
            filtered_tasks = [task for task in filtered_tasks 
                            if task.category == category_filter]
        
        # Priority filter
        priority_filter = self.filter_priority.get()
        if priority_filter != "All":
            filtered_tasks = [task for task in filtered_tasks 
                            if task.priority == priority_filter]
        
        # Status filter
        status_filter = self.filter_status.get()
        if status_filter == "Completed":
            filtered_tasks = [task for task in filtered_tasks if task.completed]
        elif status_filter == "Pending":
            filtered_tasks = [task for task in filtered_tasks if not task.completed]
        
        return filtered_tasks
    
    def refresh_task_list(self):
        """Refresh the task list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get filtered tasks
        filtered_tasks = self.get_filtered_tasks()
        
        # Sort tasks by priority and due date
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        filtered_tasks.sort(key=lambda x: (
            x.completed,  # Completed tasks go last
            priority_order.get(x.priority, 4),  # Sort by priority
            x.due_date if x.due_date else "9999-12-31"  # Sort by due date
        ))
        
        # Add tasks to treeview
        for task in filtered_tasks:
            status = "✅ Completed" if task.completed else "⏳ Pending"
            priority_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
            
            # Check if task is overdue
            overdue = ""
            if task.due_date and not task.completed:
                try:
                    due_date = datetime.strptime(task.due_date, '%Y-%m-%d')
                    if due_date.date() < datetime.now().date():
                        overdue = " ⚠️ OVERDUE"
                except ValueError:
                    pass
            
            self.tree.insert('', 'end', values=(
                task.id,  # Hidden ID for reference
                f"{priority_icon.get(task.priority, '')} {task.title}",
                task.category,
                task.priority,
                task.due_date + overdue,
                status
            ))
        
        # Update statistics
        self.update_statistics()
    
    def update_statistics(self):
        """Update statistics display"""
        total_tasks = len(self.tasks)
        completed_tasks = len([task for task in self.tasks if task.completed])
        pending_tasks = total_tasks - completed_tasks
        
        # Calculate overdue tasks
        overdue_tasks = 0
        for task in self.tasks:
            if task.due_date and not task.completed:
                try:
                    due_date = datetime.strptime(task.due_date, '%Y-%m-%d')
                    if due_date.date() < datetime.now().date():
                        overdue_tasks += 1
                except ValueError:
                    pass
        
        stats_text = f"""📊 Statistics
Total: {total_tasks}
Completed: {completed_tasks}
Pending: {pending_tasks}
Overdue: {overdue_tasks}"""
        
        self.stats_label.config(text=stats_text)
    
    def show_detailed_stats(self):
        """Show detailed statistics window"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Detailed Statistics")
        stats_window.geometry("600x500")
        stats_window.configure(bg='#2c3e50')
        stats_window.grab_set()
        
        # Create scrollable text widget
        text_widget = tk.Text(stats_window, wrap=tk.WORD, font=('Arial', 12), 
                             bg='#ecf0f1', fg='#2c3e50', padx=20, pady=20)
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Calculate detailed statistics
        total_tasks = len(self.tasks)
        completed_tasks = len([task for task in self.tasks if task.completed])
        pending_tasks = total_tasks - completed_tasks
        
        # Category breakdown
        category_stats = {}
        for task in self.tasks:
            if task.category not in category_stats:
                category_stats[task.category] = {'total': 0, 'completed': 0}
            category_stats[task.category]['total'] += 1
            if task.completed:
                category_stats[task.category]['completed'] += 1
        
        # Priority breakdown
        priority_stats = {}
        for task in self.tasks:
            if task.priority not in priority_stats:
                priority_stats[task.priority] = {'total': 0, 'completed': 0}
            priority_stats[task.priority]['total'] += 1
            if task.completed:
                priority_stats[task.priority]['completed'] += 1
        
        # Overdue tasks
        overdue_tasks = []
        for task in self.tasks:
            if task.due_date and not task.completed:
                try:
                    due_date = datetime.strptime(task.due_date, '%Y-%m-%d')
                    if due_date.date() < datetime.now().date():
                        overdue_tasks.append(task)
                except ValueError:
                    pass
        
        # Format statistics
        stats_text = f"""DETAILED STATISTICS
{'='*60}

OVERVIEW
Total Tasks: {total_tasks}
Completed Tasks: {completed_tasks}
Pending Tasks: {pending_tasks}
Completion Rate: {(completed_tasks/total_tasks*100):.1f}% if total_tasks > 0 else 0.0%

CATEGORY BREAKDOWN
{'-'*30}
"""
        
        for category, stats in category_stats.items():
            completion_rate = (stats['completed']/stats['total']*100) if stats['total'] > 0 else 0
            stats_text += f"{category}: {stats['completed']}/{stats['total']} ({completion_rate:.1f}%)\n"
        
        stats_text += f"""
PRIORITY BREAKDOWN
{'-'*30}
"""
        
        for priority, stats in priority_stats.items():
            completion_rate = (stats['completed']/stats['total']*100) if stats['total'] > 0 else 0
            stats_text += f"{priority}: {stats['completed']}/{stats['total']} ({completion_rate:.1f}%)\n"
        
        stats_text += f"""
OVERDUE TASKS
{'-'*30}
"""
        
        if overdue_tasks:
            for task in overdue_tasks:
                stats_text += f"• {task.title} (Due: {task.due_date})\n"
        else:
            stats_text += "No overdue tasks! 🎉\n"
        
        text_widget.insert(1.0, stats_text)
        text_widget.config(state='disabled')
    
    def export_tasks(self):
        """Export tasks to a text file"""
        if not self.tasks:
            messagebox.showinfo("Info", "No tasks to export!")
            return
        
        try:
            filename = f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("TASK MANAGER EXPORT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Tasks: {len(self.tasks)}\n\n")
                
                # Group tasks by category
                categories = {}
                for task in self.tasks:
                    if task.category not in categories:
                        categories[task.category] = []
                    categories[task.category].append(task)
                
                for category, tasks in categories.items():
                    f.write(f"\n{category.upper()} TASKS\n")
                    f.write("-" * 30 + "\n")
                    
                    for task in tasks:
                        f.write(f"Title: {task.title}\n")
                        f.write(f"Description: {task.description if task.description else 'No description'}\n")
                        f.write(f"Priority: {task.priority}\n")
                        f.write(f"Due Date: {task.due_date if task.due_date else 'No due date'}\n")
                        f.write(f"Status: {'Completed' if task.completed else 'Pending'}\n")
                        f.write(f"Created: {task.created_at}\n")
                        if task.completed_at:
                            f.write(f"Completed: {task.completed_at}\n")
                        f.write("-" * 20 + "\n")
            
            messagebox.showinfo("Success", f"Tasks exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export tasks: {str(e)}")
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([task.to_dict() for task in self.tasks], f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def load_tasks(self):
        """Load tasks from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(task_data) for task_data in data]
        except Exception as e:
            print(f"Error loading tasks: {e}")
            self.tasks = []
    
    def auto_save_loop(self):
        """Auto-save tasks every 30 seconds"""
        while True:
            time.sleep(30)
            self.save_tasks()
    
    def on_closing(self):
        """Handle application closing"""
        self.save_tasks()
        self.root.destroy()

class TaskNotificationSystem:
    """Advanced notification system for tasks"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.notification_thread = threading.Thread(target=self.check_notifications, daemon=True)
        self.notification_thread.start()
    
    def check_notifications(self):
        """Check for task notifications"""
        while True:
            try:
                current_time = datetime.now()
                
                for task in self.task_manager.tasks:
                    if task.completed or not task.due_date:
                        continue
                    
                    try:
                        due_date = datetime.strptime(task.due_date, '%Y-%m-%d')
                        days_until_due = (due_date.date() - current_time.date()).days
                        
                        # Notify for tasks due today or overdue
                        if days_until_due <= 0:
                            self.show_notification(task, "overdue" if days_until_due < 0 else "due_today")
                        elif days_until_due == 1:
                            self.show_notification(task, "due_tomorrow")
                        elif days_until_due <= 3:
                            self.show_notification(task, "due_soon")
                    
                    except ValueError:
                        continue
                
                time.sleep(3600)  # Check every hour
            
            except Exception as e:
                print(f"Notification error: {e}")
                time.sleep(3600)
    
    def show_notification(self, task, notification_type):
        """Show notification for a task"""
        messages = {
            "overdue": f"⚠️ OVERDUE: {task.title}",
            "due_today": f"📅 DUE TODAY: {task.title}",
            "due_tomorrow": f"📅 DUE TOMORROW: {task.title}",
            "due_soon": f"📅 DUE SOON: {task.title}"
        }
        
        message = messages.get(notification_type, f"Reminder: {task.title}")
        
        # Create notification window
        notification = tk.Toplevel(self.task_manager.root)
        notification.title("Task Reminder")
        notification.geometry("400x200")
        notification.configure(bg='#e74c3c' if notification_type == "overdue" else '#f39c12')
        notification.attributes('-topmost', True)
        
        # Center the notification
        notification.update_idletasks()
        x = (notification.winfo_screenwidth() - notification.winfo_width()) // 2
        y = (notification.winfo_screenheight() - notification.winfo_height()) // 2
        notification.geometry(f"+{x}+{y}")
        
        # Message
        ttk.Label(notification, text=message, font=('Arial', 14, 'bold'),
                 background=notification['bg'], foreground='white').pack(pady=20)
        
        # Task details
        details = f"Priority: {task.priority}\nDue: {task.due_date}"
        ttk.Label(notification, text=details, font=('Arial', 12),
                 background=notification['bg'], foreground='white').pack(pady=10)
        
        # Close button
        ttk.Button(notification, text="Close", 
                  command=notification.destroy).pack(pady=10)
        
        # Auto-close after 10 seconds
        notification.after(10000, notification.destroy)

class TaskImportExport:
    """Advanced import/export functionality"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
    
    def import_from_csv(self, filename):
        """Import tasks from CSV file"""
        try:
            import csv
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                imported_count = 0
                
                for row in reader:
                    try:
                        task = Task(
                            title=row.get('Title', ''),
                            description=row.get('Description', ''),
                            category=row.get('Category', 'General'),
                            priority=row.get('Priority', 'Medium'),
                            due_date=row.get('Due Date', ''),
                            completed=row.get('Completed', '').lower() == 'true'
                        )
                        self.task_manager.tasks.append(task)
                        imported_count += 1
                    except Exception as e:
                        print(f"Error importing row: {e}")
                
                self.task_manager.refresh_task_list()
                self.task_manager.save_tasks()
                return imported_count
                
        except Exception as e:
            raise Exception(f"Failed to import CSV: {str(e)}")
    
    def export_to_csv(self, filename):
        """Export tasks to CSV file"""
        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Title', 'Description', 'Category', 'Priority', 'Due Date', 
                             'Completed', 'Created At', 'Completed At']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for task in self.task_manager.tasks:
                    writer.writerow({
                        'Title': task.title,
                        'Description': task.description,
                        'Category': task.category,
                        'Priority': task.priority,
                        'Due Date': task.due_date,
                        'Completed': task.completed,
                        'Created At': task.created_at,
                        'Completed At': task.completed_at or ''
                    })
            
            return len(self.task_manager.tasks)
            
        except Exception as e:
            raise Exception(f"Failed to export CSV: {str(e)}")

class TaskAnalytics:
    """Advanced analytics for task management"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
    
    def get_productivity_metrics(self):
        """Calculate productivity metrics"""
        if not self.task_manager.tasks:
            return {}
        
        completed_tasks = [task for task in self.task_manager.tasks if task.completed]
        total_tasks = len(self.task_manager.tasks)
        
        # Calculate completion rate
        completion_rate = (len(completed_tasks) / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Calculate average completion time
        completion_times = []
        for task in completed_tasks:
            if task.completed_at and task.created_at:
                try:
                    created = datetime.strptime(task.created_at, '%Y-%m-%d %H:%M:%S')
                    completed = datetime.strptime(task.completed_at, '%Y-%m-%d %H:%M:%S')
                    completion_times.append((completed - created).days)
                except ValueError:
                    continue
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Tasks by priority
        priority_breakdown = {}
        for task in self.task_manager.tasks:
            if task.priority not in priority_breakdown:
                priority_breakdown[task.priority] = {'total': 0, 'completed': 0}
            priority_breakdown[task.priority]['total'] += 1
            if task.completed:
                priority_breakdown[task.priority]['completed'] += 1
        
        # Tasks by category
        category_breakdown = {}
        for task in self.task_manager.tasks:
            if task.category not in category_breakdown:
                category_breakdown[task.category] = {'total': 0, 'completed': 0}
            category_breakdown[task.category]['total'] += 1
            if task.completed:
                category_breakdown[task.category]['completed'] += 1
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': len(completed_tasks),
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'priority_breakdown': priority_breakdown,
            'category_breakdown': category_breakdown
        }
    
    def show_analytics_window(self):
        """Show analytics window"""
        analytics_window = tk.Toplevel(self.task_manager.root)
        analytics_window.title("Task Analytics")
        analytics_window.geometry("800x600")
        analytics_window.configure(bg='#2c3e50')
        analytics_window.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(analytics_window)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Overview tab
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text='Overview')
        
        # Productivity tab
        productivity_frame = ttk.Frame(notebook)
        notebook.add(productivity_frame, text='Productivity')
        
        # Trends tab
        trends_frame = ttk.Frame(notebook)
        notebook.add(trends_frame, text='Trends')
        
        # Get metrics
        metrics = self.get_productivity_metrics()
        
        # Overview tab content
        overview_text = tk.Text(overview_frame, wrap=tk.WORD, font=('Arial', 12))
        overview_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        overview_content = f"""TASK ANALYTICS OVERVIEW
{'='*50}

GENERAL METRICS
Total Tasks: {metrics.get('total_tasks', 0)}
Completed Tasks: {metrics.get('completed_tasks', 0)}
Completion Rate: {metrics.get('completion_rate', 0):.1f}%
Average Completion Time: {metrics.get('avg_completion_time', 0):.1f} days

PRIORITY BREAKDOWN
{'-'*30}
"""
        
        for priority, stats in metrics.get('priority_breakdown', {}).items():
            rate = (stats['completed']/stats['total']*100) if stats['total'] > 0 else 0
            overview_content += f"{priority}: {stats['completed']}/{stats['total']} ({rate:.1f}%)\n"
        
        overview_content += f"""
CATEGORY BREAKDOWN
{'-'*30}
"""
        
        for category, stats in metrics.get('category_breakdown', {}).items():
            rate = (stats['completed']/stats['total']*100) if stats['total'] > 0 else 0
            overview_content += f"{category}: {stats['completed']}/{stats['total']} ({rate:.1f}%)\n"
        
        overview_text.insert(1.0, overview_content)
        overview_text.config(state='disabled')

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = AdvancedTaskManager(root)
    
    # Initialize additional features
    notification_system = TaskNotificationSystem(app)
    import_export = TaskImportExport(app)
    analytics = TaskAnalytics(app)
    
    # Add import/export buttons to the main interface
    def add_import_export_buttons():
        # Create additional buttons frame
        extra_buttons_frame = ttk.Frame(app.root, style='Custom.TFrame')
        extra_buttons_frame.pack(fill='x', padx=20, pady=5)
        
        def import_csv():
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Import Tasks from CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                try:
                    count = import_export.import_from_csv(filename)
                    messagebox.showinfo("Success", f"Imported {count} tasks successfully!")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        
        def export_csv():
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Export Tasks to CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                try:
                    count = import_export.export_to_csv(filename)
                    messagebox.showinfo("Success", f"Exported {count} tasks successfully!")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        
        ttk.Button(extra_buttons_frame, text="📥 Import CSV", 
                  command=import_csv, style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(extra_buttons_frame, text="📤 Export CSV", 
                  command=export_csv, style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(extra_buttons_frame, text="📊 Analytics", 
                  command=analytics.show_analytics_window, style='Action.TButton').pack(side='left', padx=5)
    
    # Add the buttons after a short delay to ensure the main interface is ready
    root.after(100, add_import_export_buttons)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()