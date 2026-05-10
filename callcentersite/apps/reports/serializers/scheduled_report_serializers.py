"""
Serializers for ScheduledReport and SavedView.
"""
from rest_framework import serializers
from apps.reports.models import ScheduledReport, SavedView


class ScheduledReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'report', 'cron_expression', 'is_active',
            'last_run_at', 'next_run_at', 'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'last_run_at']


class SavedViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedView
        fields = [
            'id', 'name', 'report', 'filters',
            'columns', 'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']
