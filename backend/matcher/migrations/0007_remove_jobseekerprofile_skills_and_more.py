# Generated by Django 5.2.4 on 2025-07-29 20:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matcher', '0006_resumetemplateversion_userresumetemplate_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobseekerprofile',
            name='skills',
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='notice_period',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='personal_website',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='professional_summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='references',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='twitter',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='jobseekerprofile',
            name='availability',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('organization', models.CharField(blank=True, max_length=255)),
                ('date', models.CharField(blank=True, max_length=20)),
                ('description', models.TextField(blank=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='awards', to='matcher.jobseekerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Certification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('organization', models.CharField(blank=True, max_length=255)),
                ('issue_date', models.CharField(blank=True, max_length=20)),
                ('expiry_date', models.CharField(blank=True, max_length=20)),
                ('credential_id', models.CharField(blank=True, max_length=100)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='matcher.jobseekerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('degree', models.CharField(max_length=255)),
                ('institution', models.CharField(max_length=255)),
                ('year', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField(blank=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education', to='matcher.jobseekerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('technologies', models.CharField(blank=True, max_length=255)),
                ('link', models.URLField(blank=True)),
                ('start_date', models.CharField(blank=True, max_length=20)),
                ('end_date', models.CharField(blank=True, max_length=20)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='matcher.jobseekerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='VolunteerExperience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=255)),
                ('organization', models.CharField(blank=True, max_length=255)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('start_date', models.CharField(blank=True, max_length=20)),
                ('end_date', models.CharField(blank=True, max_length=20)),
                ('description', models.TextField(blank=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volunteer_experience', to='matcher.jobseekerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='WorkExperience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_title', models.CharField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('start_date', models.CharField(blank=True, max_length=20)),
                ('end_date', models.CharField(blank=True, max_length=20)),
                ('current', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_experience', to='matcher.jobseekerprofile')),
            ],
        ),
    ]
