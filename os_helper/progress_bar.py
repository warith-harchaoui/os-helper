"""
This module provides the `ProgressTask` class to display progress bars for tasks with estimated durations,
using either the `tqdm` library for console output, `stqdm` for Streamlit integration, or both simultaneously.
It also allows for silent task execution, suppressing console output and logging.

Requirements:
- `tqdm` (for console progress bar)
- `stqdm` and `streamlit` (optional, for Streamlit progress bar)

Example usage:
    def example_task(arg1, arg2):
        print(f"Executing task with: {arg1}, {arg2}")
        time.sleep(5)
    
    task = ProgressTask(task=partial(example_task, "Hello", "World"), estimated_duration=5, total_steps=50)
    task.run_with_tqdm()  # For console-only progress bar
    # task.run_with_stqdm()       # For Streamlit-only progress bar
    # task.run_with_both()        # For both console and Streamlit progress bars
"""

import time
import threading
import contextlib
import io
import logging
from typing import Callable, Optional, Union
from functools import partial
from tqdm import tqdm
import .main as osh

# Import stqdm and streamlit if available
try:
    from stqdm import stqdm
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


class ProgressTask:
    """
    A class for managing progress bars and running tasks with estimated completion times.
    Supports both `tqdm` (console) and `stqdm` (Streamlit) progress bars.

    Parameters
    ----------
    task : Callable
        The function representing the task to perform.
    estimated_duration : float
        Estimated time the task is expected to take, in seconds.
    total_steps : int, optional
        Number of steps for the progress bar, by default 100.
    desc : str, optional
        Description to display next to the progress bar, by default "Processing...".
    mininterval : float, optional
        Minimum interval between updates, in seconds, by default 0.1.
    maxinterval : float, optional
        Maximum interval between updates, in seconds, by default 1.0.
    leave : bool, optional
        Whether to leave the progress bar visible after completion, by default True.
    smoothing : float, optional
        Smoothing factor for progress bar updates (between 0 and 1), by default 0.3.
    bar_format : str, optional
        Custom format for the progress bar, by default "{l_bar}{bar}| {n_fmt}/{total_fmt}".
    progress_threshold : float, optional
        Fraction of the progress bar to reach before task completion (0 < progress_threshold < 1), by default 0.9.

    Raises
    ------
    ValueError
        If `progress_threshold` is not between 0 and 1.
    """
    
    def __init__(self, 
                 task: Callable, 
                 estimated_duration: float, 
                 total_steps: int = 100, 
                 desc: str = "Processing...", 
                 mininterval: float = 0.1, 
                 maxinterval: float = 1.0, 
                 leave: bool = True, 
                 smoothing: float = 0.3, 
                 bar_format: str = "{l_bar}{bar}| {n_fmt}/{total_fmt}", 
                 progress_threshold: float = 0.9):
        if not (0 < progress_threshold < 1):
            osh.error("progress_threshold must be between 0 and 1.")
        
        # Task properties and configuration
        self.task = task
        self.duration = estimated_duration
        self.total_steps = total_steps
        self.desc = desc
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.leave = leave
        self.smoothing = smoothing
        self.bar_format = bar_format
        self.progress_threshold = progress_threshold
        self.completion_threshold = 1 - progress_threshold  # Automatically calculate completion threshold

    def _run_progress_bar(self, progress_bar: Union[tqdm, Callable[..., None]]) -> None:
        """
        Runs the specified progress bar up to the configured threshold, then waits to set to 100% upon task completion.

        Parameters
        ----------
        progress_bar : Union[tqdm, Callable[..., None]]
            The progress bar function to use (e.g., `tqdm` or `stqdm`).
        """
        threshold_steps = int(self.total_steps * self.progress_threshold)
        with progress_bar(
            total=self.total_steps, 
            desc=self.desc, 
            mininterval=self.mininterval, 
            maxinterval=self.maxinterval, 
            leave=self.leave, 
            smoothing=self.smoothing, 
            bar_format=self.bar_format
        ) as progress:
            # Update progress bar up to the threshold
            for _ in range(threshold_steps):
                time.sleep(self.duration / self.total_steps)
                progress.update(1)
            
            # Wait for task completion before setting to 100%
            while not self.task_complete:
                time.sleep(0.1)
            
            # Set progress to 100% once the task is fully complete
            progress.n = self.total_steps
            progress.refresh()

    def _run_task(self) -> None:
        """
        Executes the actual task, silencing its output.
        """
        self.task_complete = False  # Flag to indicate task completion
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            logging_level = logging.getLogger().level
            logging.getLogger().setLevel(logging.CRITICAL + 1)
            try:
                self.task()
            finally:
                logging.getLogger().setLevel(logging_level)
                self.task_complete = True  # Set task completion flag

    def run_with_tqdm(self) -> None:
        """
        Runs the task with a console (tqdm) progress bar.
        """
        progress_thread = threading.Thread(target=self._run_progress_bar, args=(tqdm,))
        task_thread = threading.Thread(target=self._run_task)
        
        progress_thread.start()
        task_thread.start()
        
        progress_thread.join()
        task_thread.join()

    def run_with_stqdm(self) -> None:
        """
        Runs the task with a Streamlit (stqdm) progress bar.
        
        Raises
        ------
        ImportError
            If `stqdm` or `streamlit` is not available.
        """
        if not HAS_STREAMLIT:
            osh.error("stqdm or streamlit is not available. Please install them to use this feature.")
        
        progress_thread = threading.Thread(target=self._run_progress_bar, args=(stqdm,))
        task_thread = threading.Thread(target=self._run_task)
        
        progress_thread.start()
        task_thread.start()
        
        progress_thread.join()
        task_thread.join()

    def run_with_both(self) -> None:
        """
        Runs the task with both console (tqdm) and Streamlit (stqdm) progress bars in separate threads.

        Raises
        ------
        ImportError
            If `stqdm` or `streamlit` is not available.
        """
        if not HAS_STREAMLIT:
            osh.error("stqdm or streamlit is not available. Please install them to use this feature.")
        
        # Run both tqdm and stqdm in separate threads
        console_thread = threading.Thread(target=self._run_progress_bar, args=(tqdm,))
        streamlit_thread = threading.Thread(target=self._run_progress_bar, args=(stqdm,))
        task_thread = threading.Thread(target=self._run_task)

        console_thread.start()
        streamlit_thread.start()
        task_thread.start()

        console_thread.join()
        streamlit_thread.join()
        task_thread.join()


def my_custom_task(arg1: str, arg2: str) -> None:
    """
    A custom task function that includes print statements and logging messages.

    Parameters
    ----------
    arg1 : str
        First argument for the task.
    arg2 : str
        Second argument for the task.
    """
    print(f"Running task with arguments: {arg1}, {arg2}")
    logging.info("This is an info log message.")
    logging.warning("This is a warning message.")
    time.sleep(5)


if __name__ == "__main__":
    # Configure the task with partial and set arguments for my_custom_task
    task_with_args = partial(my_custom_task, arg1="Hello", arg2="World")

    # Initialize the ProgressTask class with adjustable progress threshold
    progress_task = ProgressTask(task=task_with_args, estimated_duration=5, total_steps=50, progress_threshold=0.85)

    # Choose one of the following to run:
    # progress_task.run_with_tqdm()        # For console-only progress bar
    # progress_task.run_with_stqdm()       # For Streamlit-only progress bar
    # progress_task.run_with_both()        # For both console and Streamlit progress bars
