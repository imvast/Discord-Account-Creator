from .challenges import Challenge
from .exceptions import ApiError, SolveFailed
import os
import threading
import time
import redis

class Solver:
    def __init__(self, database=None, collect_data=True,
                 min_answers=1, max_tasks=0, debug=False):
        database = database if database is not None else redis.Redis()

        self.database = database
        self.collect_data = collect_data
        self.min_answers = min_answers
        self.max_tasks = max_tasks
        self.debug = debug

    @staticmethod
    def _get_task_id(challenge, task, http_client=None):
        if challenge.type == "image_label_binary" and challenge.question.startswith("Please click each image containing a"):
            category = challenge.question.rsplit(" ", 1)[-1].lower().strip("?,.!")
            image_hash = task.phash(8, http_client=http_client)
            return f"{category}_{image_hash}"
        
        raise SolveFailed("Unsupported challenge")
    
    def _get_task_score(self, task_id):
        score = self.database.get(task_id)
        if score:
            score = int(score)
        else:
            score = 0
        return score

    def _increment_task_score(self, task_id, delta):
        self.database.incrby(task_id, delta)
        if self.debug:
            print("INCR", task_id, delta, self._get_task_score(task_id))

    def get_token(self, sitekey, page_url, http_client2=None,
                  **ch_kwargs):
        ch = Challenge(sitekey, page_url, **ch_kwargs)

        if ch.token:
            return ch.token

        if ch.type != "image_label_binary":
            raise SolveFailed(
                f"Challenge type '{ch.type}' is not supported")
        
        if self.max_tasks and len(ch.tasks) > self.max_tasks:
            raise SolveFailed(
                f"Challenge has too many tasks ({len(ch.tasks)} > {self.max_tasks})")
        
        task_to_id = {
            task: self._get_task_id(ch, task, http_client2)
            for task in ch.tasks
        }
        task_scores = sorted([
            (task, self._get_task_score(task_to_id[task]))
            for task in ch.tasks
        ], key=lambda x: x[1], reverse=True)

        answers = []
        for task, score in task_scores:
            if score > 0:
                answers.append(task)
        
        if self.min_answers:
            while task_scores and self.min_answers > len(answers):
                task, score = task_scores.pop(0)
                if not task in answers:
                    answers.append(task)

        if not answers:
            return
        
        token = None
        try:
            token = ch.solve(answers)
        except ApiError:
            pass
        
        if self.collect_data:
            for task in answers:
                task_id = task_to_id[task]
                task_score = self._get_task_score(task_id)
                if token:
                    self._increment_task_score(task_id, 1)
            
        return token