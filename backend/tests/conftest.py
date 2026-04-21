import pytest
import sys
import os

# Mock Supabase before imports
class MockSupabase:
    def table(self, name):
        return self
    def select(self, *args):
        return self
    def eq(self, *args):
        return self
    def execute(self):
        class Result:
            data = []
        return Result()
    def insert(self, *args):
        return self

sys.modules['supabase'] = type('MockModule', (), {'create_client': lambda *args: MockSupabase()})()
