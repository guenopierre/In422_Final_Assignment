# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 08:19:29 2026

@author: Pierre Guéno
"""

import numpy as np

def ppcm(a, b):
    max_num = max(a, b)
    while True:
        if max_num % a == 0 and max_num % b == 0:
            return max_num
        max_num += 1

def ppcm_tuple(T):
    if not T:
        return 0  # or raise an exception if the tuple is empty
    result = T[0]
    for num in T[1:]:
        result = ppcm(result, num)
    return result

def schedule_to_string(schedule, execution_time):
    """
    Converts a schedule matrix into a string.

    For each time unit, writes J<task_number><instance_number>
    where the instance number counts how many times the task has been activated
    (one instance = one complete execution of duration execution_time[i]).
    The counter increments only at the start of a new instance,
    not at each time unit.

    Consecutive identical tokens are merged: if the same task
    runs over several contiguous slots of the same instance, the token
    is written only once.

    Parameters
    ----------
    schedule : np.ndarray
        Matrix (n_tasks, hyperperiod) with 1 where the task runs, 0 otherwise.
    execution_time : tuple, list
        Execution time Ci of each task (same order as the rows of the schedule matrix).

    Returns
    -------
    str
        String summarizing the schedule, e.g.: "J11 J21 J31 J41 J51 J12 ..."
        Idle CPU slots are represented by "--" (also merged if consecutive).
    """
    n, hyperperiod = schedule.shape
    C = list(execution_time)
    instance_counts = [0] * n   # number of instances already started for each task
    progress = [0] * n          # time units already completed in the current instance
    tokens = []

    for t in range(hyperperiod):
        active = None
        for i in range(n):
            if schedule[i][t] == 1:
                active = i
                break

        if active is None:
            token = "--"
        else:
            # If we are at the very beginning of a new instance, increment the counter
            if progress[active] == 0:
                instance_counts[active] += 1
            token = f"J{active + 1}{instance_counts[active]}"
            progress[active] += 1
            # When Ci units have been reached, the instance is complete: reset progress to 0
            if progress[active] >= C[active]:
                progress[active] = 0

        # Avoid consecutive duplicates
        if not tokens or tokens[-1] != token:
            tokens.append(token)

    return " ".join(tokens)

def round_robin(tasks, C, T):
    """
    Each task takes turns to execute in a fixed order.

    Parameters
    ----------
    tasks : tuple, list
        numbers of tasks
    execution_time : tuple, list
        execution time of each task in the same order than 1st tuple
    period : tuple, list
        execution period of each task in the same order than 1st tuple

    Returns
    -------
    schedulable : bool
        True if the task set is schedulable with Round Robin, False otherwise.
    schedule : np.ndarray or None
        Matrix of shape (n_tasks, hyperperiod) with 1 where a task runs, else 0.
        None if not schedulable.
    waiting_time : int or None
        Number of idle CPU slots over the hyperperiod. None if not schedulable.
    schedule_str : str or None
        String summarizing the schedule (e.g. "J11 J21 J22 J23 ...").
        None if not schedulable.

    """
    n = len(tasks)
    C = list(C)
    T = list(T)
    # Schedulability check


    hyperperiod = ppcm_tuple(T)
    # Condition 1: CPU utilization <= 1
    utilization = sum(c / t for c, t in zip(C, T))
    # Condition 2: a full cycle (sum Ci) must fit within the LCM of periods
    sum_C = sum(C)

    schedulable = utilization <= 1.0 and sum_C <= hyperperiod

    if not schedulable:
        print("Round Robin: NOT schedulable")
        if utilization > 1.0:
            print(f"  CPU utilization = {utilization:.4f} > 1")
        if sum_C > hyperperiod:
            print(f"  sum(Ci) = {sum_C} > LCM(Ti) = {hyperperiod}")
        return False, None, None, None



    # --- Build the schedule matrix ---
    schedule = np.zeros((n, hyperperiod))

    remaining = [0] * n  # remaining work for each task
    rr_idx = 0           # index of the current task in the round-robin queue
    rr_left = 0          # remaining time units for the current task

    for t in range(hyperperiod):
        # Job arrivals at the start of the time unit
        for i in range(n):
            if t % T[i] == 0:
                remaining[i] += C[i]

        # If the current slot is exhausted, move to the next task
        if rr_left == 0:
            found = False
            for k in range(n):
                idx = (rr_idx + k) % n
                if remaining[idx] > 0:
                    rr_idx = idx
                    rr_left = remaining[idx]
                    found = True
                    break
            if not found:
                continue  # CPU idle

        # Execute the current task for 1 time unit
        schedule[rr_idx][t] = 1
        remaining[rr_idx] -= 1
        rr_left -= 1
        if rr_left == 0:
            rr_idx = (rr_idx + 1) % n

    waiting_time = int(np.all(schedule == 0, axis=0).sum())
    schedule_str = schedule_to_string(schedule, C)

    return True, schedule, waiting_time, schedule_str

def rate_monotonic(tasks, execution_time, period):
    """
    Tasks with higher frequency (shorter periods) have higher priority.

    Parameters
    ----------
    tasks : tuple, list
        numbers of tasks
    execution_time : tuple, list
        execution time of each task in the same order than 1st tuple
    period : tuple, list
        execution period of each task in the same order than 1st tuple

    Returns
    -------
    schedulable : bool
        True if the task set is schedulable with Rate Monotonic, False otherwise.
    schedule : np.ndarray or None
        Matrix of shape (n_tasks, hyperperiod) with 1 where a task runs, else 0.
        None if not schedulable.
    waiting_time : int or None
        Number of idle CPU slots over the hyperperiod. None if not schedulable.
    schedule_str : str or None
        String summarizing the schedule (e.g. "J11 J21 J22 J23 ...").
        None if not schedulable.

    """
    n = len(tasks)
    C = list(execution_time)
    T = list(period)

    # Schedulability check (Liu & Layland criterion)
    utilization = sum(c / t for c, t in zip(C, T))
    rm_bound = n * (2 ** (1 / n) - 1)

    schedulable = utilization <= rm_bound

    if not schedulable:
        print("Rate Monotonic: NOT schedulable")
        return False, None, None, None

    # Priorities: shorter period = higher priority
    # Sort indices by ascending period (index 0 = highest priority)
    priority_order = sorted(range(n), key=lambda i: T[i])

    hyperperiod = ppcm_tuple(T)
    schedule = np.zeros((n, hyperperiod), dtype=int)

    remaining = [0] * n  # remaining work for each task at time t

    for t in range(hyperperiod):
        # Job arrivals at the start of the time unit
        for i in range(n):
            if t % T[i] == 0:
                remaining[i] += C[i]

        # Choose the ready task with the highest priority (shortest period)
        chosen = None
        for idx in priority_order:
            if remaining[idx] > 0:
                chosen = idx
                break

        if chosen is not None:
            schedule[chosen][t] = 1
            remaining[chosen] -= 1

    waiting_time = int(np.all(schedule == 0, axis=0).sum())
    schedule_str = schedule_to_string(schedule, C)

    return True, schedule, waiting_time, schedule_str

def earliest_deadline_first(tasks, execution_time, period):
    """
    The task with the earliest deadline is executed first.

    Parameters
    ----------
    tasks : tuple, list
        numbers of tasks
    execution_time : tuple, list
        execution time of each task in the same order than 1st tuple
    period : tuple, list
        execution period of each task in the same order than 1st tuple

    Returns
    -------
    schedulable : bool
        True if the task set is schedulable with EDF, False otherwise.
    schedule : np.ndarray or None
        Matrix of shape (n_tasks, hyperperiod) with 1 where a task runs, else 0.
        None if not schedulable.
    waiting_time : int or None
        Number of idle CPU slots over the hyperperiod. None if not schedulable.
    schedule_str : str or None
        String summarizing the schedule (e.g. "J11 J21 J22 J23 ...").
        None if not schedulable.

    """
    n = len(tasks)
    C = list(execution_time)
    T = list(period)

    # Schedulability check (necessary and sufficient condition for EDF)
    utilization = sum(c / t for c, t in zip(C, T))

    schedulable = utilization <= 1.0

    if not schedulable:
        print("Earliest Deadline First: NOT schedulable")
        return False, None, None, None

    hyperperiod = ppcm_tuple(T)
    schedule = np.zeros((n, hyperperiod), dtype=int)

    remaining  = [0] * n        # remaining work for each task
    deadline   = [None] * n     # next absolute deadline for each task

    for t in range(hyperperiod):
        # Job arrivals at the start of the time unit
        for i in range(n):
            if t % T[i] == 0:
                remaining[i] += C[i]
                deadline[i] = t + T[i]   # deadline = activation + period

        # Choose the ready task with the earliest absolute deadline (dynamic priority)
        chosen = None
        earliest = float('inf')
        for i in range(n):
            if remaining[i] > 0 and deadline[i] < earliest:
                earliest = deadline[i]
                chosen = i

        if chosen is not None:
            schedule[chosen][t] = 1
            remaining[chosen] -= 1

    waiting_time = int(np.all(schedule == 0, axis=0).sum())
    schedule_str = schedule_to_string(schedule, C)

    return True, schedule, waiting_time, schedule_str
