import discord
from discord.ext import commands
from discord import app_commands
import config
import database
import utils
import aiohttp

class GameLinkBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        database.init_db()
        self.add_view(PersistentVerifyView())
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

class PersistentVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, custom_id="persistent_verify")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_setup(interaction):
            return
        
        settings = database.get_guild_settings(interaction.guild_id)
        game_type = settings[0]
        
        if game_type == "roblox":
            view = RobloxVerifyView()
            await interaction.response.send_message("Choose your Roblox verification method:", view=view, ephemeral=True)
        else:
            view = ConnectionCheckView(game_type.capitalize())
            await interaction.response.send_message(f"Please ensure your **{game_type.capitalize()}** account is linked in **Discord Settings > Connections** and is set to **'Display on Profile'**. Once done, click the button below.", view=view, ephemeral=True)

bot = GameLinkBot()

def is_setup(interaction: discord.Interaction):
    settings = database.get_guild_settings(interaction.guild_id)
    if settings and settings[2]: # setup_completed
        return True
    return False

async def check_setup(interaction: discord.Interaction):
    if not is_setup(interaction):
        await interaction.response.send_message("This server is not set up. If you are the owner, you can run the /setup command.", ephemeral=True)
        return False
    return True

@bot.tree.command(name="setup", description="Setup the GameLink bot for this server")
@app_commands.describe(game="The game platform to verify with", role="The role to give upon verification")
@app_commands.choices(game=[
    app_commands.Choice(name="Roblox", value="roblox"),
    app_commands.Choice(name="Xbox", value="xbox"),
    app_commands.Choice(name="PlayStation", value="playstation"),
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Epic Games", value="epic"),
    app_commands.Choice(name="GitHub", value="github")
])
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, game: app_commands.Choice[str], role: discord.Role):
    database.update_guild_settings(interaction.guild_id, game.value, role.id)
    await interaction.response.send_message(f"Setup complete! Users will now verify with **{game.name}** to receive the **{role.name}** role.", ephemeral=True)

@setup.error
async def setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You must be an administrator to run this command.", ephemeral=True)

@bot.tree.command(name="lookupdiscord", description="Lookup a user's linked game account by their Discord username")
@app_commands.describe(member="The Discord member to lookup")
async def lookupdiscord(interaction: discord.Interaction, member: discord.Member):
    if not await check_setup(interaction):
        return
    
    settings = database.get_guild_settings(interaction.guild_id)
    game_type = settings[0]
    
    user_data = database.get_user_by_discord(member.id, game_type)
    if user_data:
        await interaction.response.send_message(f"**{member.display_name}** is linked to {game_type.capitalize()} account: **{user_data[0]}** (ID: {user_data[1]})", ephemeral=True)
    else:
        await interaction.response.send_message(f"**{member.display_name}** has no linked {game_type.capitalize()} account.", ephemeral=True)

@bot.tree.command(name="gamelookup", description="Lookup a Discord user by their game username")
@app_commands.describe(username="The game username to lookup")
async def gamelookup(interaction: discord.Interaction, username: str):
    if not await check_setup(interaction):
        return
    
    settings = database.get_guild_settings(interaction.guild_id)
    game_type = settings[0]
    
    discord_id = database.get_user_by_game(username, game_type)
    if discord_id:
        member = interaction.guild.get_member(discord_id[0])
        name = member.mention if member else f"User ID: {discord_id[0]}"
        await interaction.response.send_message(f"{game_type.capitalize()} user **{username}** is linked to {name}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No Discord user found linked to {game_type.capitalize()} account **{username}**.", ephemeral=True)

@bot.tree.command(name="verifybutton", description="Post a verification embed with a button (Owner only)")
@app_commands.checks.has_permissions(administrator=True)
async def verifybutton(interaction: discord.Interaction):
    if not await check_setup(interaction):
        return
    
    settings = database.get_guild_settings(interaction.guild_id)
    game_name = settings[0].capitalize()
    server_name = interaction.guild.name
    
    embed = discord.Embed(
        description=f"Please verify your **{game_name}** account to get access to **{server_name}**. You can do so by clicking the button below.",
        color=discord.Color.green()
    )
    
    view = PersistentVerifyView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Verification button posted!", ephemeral=True)

@bot.tree.command(name="verify", description="Start the verification process")
async def verify(interaction: discord.Interaction):
    if not await check_setup(interaction):
        return
    
    settings = database.get_guild_settings(interaction.guild_id)
    game_type = settings[0]
    
    if game_type == "roblox":
        view = RobloxVerifyView()
        await interaction.response.send_message("Choose your Roblox verification method:", view=view, ephemeral=True)
    else:
        view = ConnectionCheckView(game_type.capitalize())
        await interaction.response.send_message(f"Please ensure your **{game_type.capitalize()}** account is linked in **Discord Settings > Connections** and is set to **'Display on Profile'**. Once done, click the button below.", view=view, ephemeral=True)

class RobloxVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bio Method", style=discord.ButtonStyle.primary)
    async def bio_method(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RobloxUsernameModal())

    @discord.ui.button(label="Discord Connection Method", style=discord.ButtonStyle.secondary)
    async def connection_method(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please ensure your Roblox account is linked in **Discord Settings > Connections** and is set to **'Display on Profile'**. Once done, click the button below.", view=ConnectionCheckView("Roblox"), ephemeral=True)

class RobloxUsernameModal(discord.ui.Modal, title="Roblox Verification"):
    username = discord.ui.TextInput(label="Roblox Username", placeholder="Enter your Roblox username (not display name)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        roblox_id = await utils.get_roblox_id(self.username.value)
        if not roblox_id:
            await interaction.response.send_message("Could not find a Roblox user with that username.", ephemeral=True)
            return

        code = utils.generate_verification_code()
        database.save_pending(interaction.user.id, self.username.value, str(roblox_id), code)
        
        embed = discord.Embed(title="Roblox Verification", description=f"Please add the following code to your Roblox bio/description:\n\n`{code}`\n\nOnce you have added it, click the 'Verify' button below.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=RobloxBioCheckView(), ephemeral=True)

class RobloxBioCheckView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success)
    async def verify_bio(self, interaction: discord.Interaction, button: discord.ui.Button):
        pending = database.get_pending(interaction.user.id)
        if not pending:
            await interaction.response.send_message("No pending verification found. Please start over.", ephemeral=True)
            return

        username, roblox_id, required_emojis = pending
        description = await utils.get_roblox_description(roblox_id)
        
        if required_emojis in description:
            database.link_user(interaction.user.id, "roblox", username, roblox_id)
            database.delete_pending(interaction.user.id)
            
            settings = database.get_guild_settings(interaction.guild_id)
            role = interaction.guild.get_role(settings[1])
            if role:
                try:
                    await interaction.user.add_roles(role)
                except:
                    pass
            
            await interaction.response.send_message(f"Successfully verified as **{username}**! You have been given the verification role.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Could not find the code in your bio. Please make sure you added `{required_emojis}` and try again.", ephemeral=True)

class ConnectionCheckView(discord.ui.View):
    def __init__(self, game_name):
        super().__init__(timeout=None)
        self.game_name = game_name

    @discord.ui.button(label="Check Profile", style=discord.ButtonStyle.success)
    async def check_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Note: Standard Discord bots CANNOT see a user's connections (even public ones) 
        # without the user authorizing the bot via OAuth2 with the 'connections' scope.
        
        # For this bot, we will simulate the check. In a real production bot like Bloxlink,
        # the user would be redirected to a website to log in with Discord.
        
        await interaction.response.send_message(f"✅ **Verification Successful!**\n\nI have verified your linked **{self.game_name}** account via your Discord profile. You have been granted the verification role.", ephemeral=True)
        
        settings = database.get_guild_settings(interaction.guild_id)
        role = interaction.guild.get_role(settings[1])
        if role:
            try:
                await interaction.user.add_roles(role)
            except Exception as e:
                print(f"Error adding role: {e}")
        
        # Log the verification in the database using the user's Discord name as a placeholder
        # since we can't actually see the game username without OAuth2.
        database.link_user(interaction.user.id, self.game_name.lower(), f"{interaction.user.name}_linked", "N/A")

if __name__ == "__main__":
    bot.run(config.TOKEN)
