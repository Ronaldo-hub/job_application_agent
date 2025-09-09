import os
import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import asyncio
import job_search
import resume_tool
import course_suggestions
from typing import Optional

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load master resume
master_resume = resume_tool.load_master_resume()

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

@bot.tree.command(name="search_jobs", description="Search for jobs with location and time filters")
@app_commands.describe(
    keywords="Job keywords (e.g., 'python developer')",
    location="Job location (optional, e.g., 'New York', 'remote', 'London')",
    max_age_days="Maximum job age in days (optional, default: 30)",
    salary_min="Minimum salary (optional)",
    salary_max="Maximum salary (optional)"
)
async def search_jobs(
    interaction: discord.Interaction,
    keywords: str,
    location: Optional[str] = None,
    max_age_days: Optional[int] = 30,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None
):
    """Search for jobs and analyze fit."""
    await interaction.response.defer()

    try:
        # Search jobs using APIs
        search_params = {
            'keywords': keywords,
            'location': location,
            'max_age_days': max_age_days,
            'salary_min': salary_min,
            'salary_max': salary_max
        }

        jobs = await job_search.search_jobs_async(search_params)

        if not jobs:
            await interaction.followup.send("No jobs found matching your criteria.")
            return

        # Analyze fit for each job
        high_fit_jobs = []
        low_fit_jobs = []

        for job in jobs:
            fit_score = resume_tool.calculate_fit_score(master_resume, job)
            job['fit_score'] = fit_score

            if fit_score >= 90:
                high_fit_jobs.append(job)
            else:
                low_fit_jobs.append(job)

        # Send results
        response = f"Found {len(jobs)} jobs for '{keywords}'"
        if location:
            response += f" in {location}"
        response += f"\n\nHigh-fit jobs (≥90%): {len(high_fit_jobs)}\nLow-fit jobs: {len(low_fit_jobs)}"

        await interaction.followup.send(response)

        # Process high-fit jobs
        for job in high_fit_jobs[:3]:  # Limit to 3 for demo
            await process_high_fit_job(interaction, job)

        # Suggest courses for skill gaps
        if low_fit_jobs:
            await suggest_courses_for_gaps(interaction, low_fit_jobs)

    except Exception as e:
        logger.error(f"Error in search_jobs: {e}")
        await interaction.followup.send(f"Error searching jobs: {str(e)}")

async def process_high_fit_job(interaction: discord.Interaction, job: dict):
    """Process a high-fit job: generate resume and notify."""
    try:
        # Generate resume
        resume = resume_tool.generate_resume(job)

        # Send notification
        embed = discord.Embed(
            title=f"High-Fit Job Match: {job['title']}",
            description=f"Company: {job['company']}\nLocation: {job['location']}\nFit Score: {job['fit_score']:.1f}%",
            color=0x00ff00
        )

        if resume['word_file']:
            # Send resume file
            await interaction.followup.send(
                embed=embed,
                file=discord.File(resume['word_file'], filename=f"{job['title'].replace(' ', '_')}_resume.docx")
            )
        else:
            await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"Error processing high-fit job: {e}")
        await interaction.followup.send(f"Error generating resume for {job['title']}: {str(e)}")

async def suggest_courses_for_gaps(interaction: discord.Interaction, low_fit_jobs: list):
    """Analyze skill gaps and suggest courses."""
    try:
        # Aggregate requirements from low-fit jobs
        all_requirements = []
        for job in low_fit_jobs:
            all_requirements.extend(job.get('requirements', []))

        # Find skill gaps
        skill_gaps = course_suggestions.analyze_skill_gaps(master_resume, all_requirements)

        if not skill_gaps:
            return

        # Get course suggestions
        course_suggestions_list = await course_suggestions.get_course_suggestions(skill_gaps)

        # Send suggestions
        embed = discord.Embed(
            title="Course Suggestions for Skill Gaps",
            description=f"Based on {len(low_fit_jobs)} job requirements",
            color=0xffa500
        )

        for gap, courses in course_suggestions_list.items():
            if courses:
                embed.add_field(
                    name=f"Gap: {gap}",
                    value="\n".join([f"• {course['title']} ({course['platform']})" for course in courses[:2]]),
                    inline=False
                )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"Error suggesting courses: {e}")
        await interaction.followup.send(f"Error generating course suggestions: {str(e)}")

@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    """Show help information."""
    embed = discord.Embed(
        title="Job Application Assistant",
        description="Available commands:",
        color=0x3498db
    )

    embed.add_field(
        name="/search_jobs",
        value="Search for jobs with keywords, location, and salary filters",
        inline=False
    )

    embed.add_field(
        name="/help",
        value="Show this help message",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    logger.error(f"Command error: {error}")
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use /help for available commands.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

async def send_notification(user_id: str, message: str, embed: discord.Embed = None):
    """Send a notification to a user."""
    try:
        user = await bot.fetch_user(int(user_id))
        if embed:
            await user.send(embed=embed)
        else:
            await user.send(message)
    except Exception as e:
        logger.error(f"Error sending notification to {user_id}: {e}")

def run_bot():
    """Run the Discord bot."""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        return

    bot.run(token)

if __name__ == "__main__":
    run_bot()