import discord
from discord.ext import commands, tasks
import random
from discord.utils import get
import asyncio
import time
from discord import app_commands
from discord.ui import View, Button
import math
from discord.ui import Select
import os
from discord import ButtonStyle, ui
from datetime import datetime, timedelta
import json


# Classe para gerenciar o banco de dados
class Database:
    def __init__(self, file_path='db.json'):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_user_data(self, user_id):
        return self.data.get(user_id, {})

    def update_user_data(self, user_id, user_data):
        self.data[user_id] = user_data
        self.save()

# Instância do banco de dados
db = Database()

# Obter o tempo atual
agora = datetime.now()
amanha = agora + timedelta(days=1)

# Exibir datas formatadas
print("Agora:", agora.strftime("%Y-%m-%d %H:%M:%S"))
print("Amanhã:", amanha.strftime("%Y-%m-%d %H:%M:%S"))

# Definir intents
intents = discord.Intents.default()
intents.message_content = True  # Ativar leitura de mensagens
intents.members = True  # Ativa a intenção de membros (necessário para acessar informações de usuários)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dicionário para armazenar os dados dos usuários na memória
users_data = {}

@bot.event
async def on_message(message):
    # Evita que o bot responda a si mesmo
    if message.author.bot:
        return

    # Verifica se o bot foi mencionado diretamente na mensagem
    if message.content.startswith(f"<@{bot.user.id}>") or message.content.startswith(f"<@!{bot.user.id}>"):
        await message.channel.send(
            f"Olá {message.author.mention}! Meu prefixo neste servidor é `!`. Para ver meus comandos, use `!cmd`."
        )

    # Processa outros comandos do bot
    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    shard_id = ctx.guild.shard_id if ctx.guild else 0  # Obtém a shard do servidor
    total_shards = bot.shard_count if bot.shard_count else 1  # Número total de shards
    cluster_name = "Luminarls Cluster"  # Nome do cluster do bot
    gateway_ping = round(bot.latency * 1000)  # Ping do gateway

    # Marca o tempo de início
    start_time = time.perf_counter()
    message = await ctx.send("🏓 Calculando latência...")  # Mensagem temporária
    api_ping = round((time.perf_counter() - start_time) * 1000)  # Calcula o tempo de resposta da API

    # Cria o embed com os valores finais
    embed = discord.Embed(color=discord.Color.purple())
    embed.add_field(
        name="🏓 | Pong!", 
        value=f"(📡 Shard {shard_id}/{total_shards}) (:lunar: {cluster_name})",
        inline=False
    )
    embed.add_field(name="⏱ | Gateway Ping", value=f"{gateway_ping}ms", inline=False)
    embed.add_field(name="⚡ | API Ping", value=f"{api_ping}ms", inline=False)

    # Edita a mensagem inicial com o embed final
    await message.edit(content=None, embed=embed)

@bot.command(name="cmd")  # Define o comando como "!cmd"
async def cmd(ctx):  
    embed = discord.Embed(
        title="Central de Comandos",
        description="Explore os comandos disponíveis do Luminarls:",
        color=discord.Color.dark_gray()
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1331060223833673819/827885bea276a81d4a5e63fbe8cc74c2.png?size=1024")

    embed.add_field(
        name="Economia", 
        value="`!luzes` - Resgate diário\n"
              "`!luz` - Ver saldo atual\n"
              "`!pay @usuário quantidade` - Transferir luzes", 
        inline=False
    )

    embed.add_field(
        name="Avatar", 
        value="`!avatar` - Veja o avatar de um usuário", 
        inline=False
    )

    embed.add_field(
        name="Ranking",
        value="`!rank luzes` - Ranking global\n"
              "Padrão: 10 usuários por página, use botões para navegar",
        inline=False
    )

    embed.add_field(
        name="Convite",
        value="`!convite` - Adicione-me ao seu servidor!",
        inline=False
    )

    embed.add_field(
        name="Mais Comandos",
        value="Use `/luzguia` para ver todos os comandos disponíveis!",
        inline=False
    )

    embed.set_footer(text="Use o prefixo `!` ou / para executar os comandos.")

    await ctx.send(embed=embed)

# Tempo de espera de 5 minutos
TEMPO_ESPERA = timedelta(minutes=5)
BASE_LUZES = 100  # Quantidade base de luzes

def calcular_luzes(base: int) -> int:
    """Calcula a quantidade de luzes coletadas com variação aleatória."""
    porcentagem = random.randint(50, 150)
    bonus_fixo = random.randint(20, 50)
    return (base * porcentagem) // 100 + bonus_fixo

def criar_usuario(user_id):
    """Cria um novo usuário no banco de dados se não existir."""
    if user_id not in db.data:
        db.data[user_id] = {"luzes": 0, "last_claimed": "2000-01-01 00:00:00"}
        db.save()

def obter_ranking():
    """Ordena os usuários pelo total de luzes."""
    return sorted(db.data.items(), key=lambda x: x[1]["luzes"], reverse=True)

@bot.command(name="luzes", aliases=["Luzes"])
async def luzes(ctx):
    """Comando para coletar luzes a cada 5 minutos e exibir contagem regressiva."""
    user_id = str(ctx.author.id)
    agora = datetime.utcnow()
    criar_usuario(user_id)

    user_data = db.get_user_data(user_id)
    ultimo_resgate = datetime.strptime(user_data.get("last_claimed", "2000-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
    tempo_passado = agora - ultimo_resgate

    if tempo_passado >= TEMPO_ESPERA:
        luzes_coletadas = calcular_luzes(BASE_LUZES)
        user_data["luzes"] += luzes_coletadas
        user_data["last_claimed"] = agora.strftime("%Y-%m-%d %H:%M:%S")
        db.update_user_data(user_id, user_data)

        ranking = obter_ranking()
        user_rank = next((i + 1 for i, (uid, _) in enumerate(ranking) if uid == user_id), "N/A")

        frases_coleta = [
            f"🎉 | {ctx.author.mention}, você coletou **{luzes_coletadas}** luzes!",
            f"✨ | Uau, {ctx.author.mention}! **{luzes_coletadas}** luzes foram adicionadas ao seu inventário!",
            f"💡 | {ctx.author.mention}, você acaba de resgatar **{luzes_coletadas}** luzes brilhantes!",
            f"🌟 | Incrível, {ctx.author.mention}! Você encontrou **{luzes_coletadas}** luzes reluzentes!",
            f"⚡ | {ctx.author.mention}, você coletou **{luzes_coletadas}** luzes energizantes!"
        ]

        frase_escolhida = random.choice(frases_coleta)

        embed = discord.Embed(
            title="✨ Luzes Coletadas! ✨",
            description=(
                f"{frase_escolhida}\n"
                f"🌟 | Total: **{user_data['luzes']:,}** luzes acumuladas.\n"
                f"🏆 | Ranking: **#{user_rank}** — Veja os líderes com `!rank luzes`"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    else:
        tempo_restante = TEMPO_ESPERA - tempo_passado
        segundos_restantes = int(tempo_restante.total_seconds())

        def format_time(seconds):
            minutos = seconds // 60
            segundos = seconds % 60
            return f"**{minutos}m {segundos}s**"

        embed = discord.Embed(
            title="⏳ Tempo de Espera",
            description=(
                f"⚠️ | {ctx.author.mention}, você já coletou luzes recentemente.\n"
                f"🕒 | Próximo resgate disponível em {format_time(segundos_restantes)}."
            ),
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        message = await ctx.send(embed=embed)

        # Atualiza a mensagem apenas a cada 10 segundos para evitar rate limit
        while segundos_restantes > 0:
            await asyncio.sleep(10)
            segundos_restantes -= 10
            if segundos_restantes <= 0:
                break  # Para evitar atualizar quando já estiver pronto

            embed.description = (
                f"⚠️ | {ctx.author.mention}, você já coletou luzes recentemente.\n"
                f"🕒 | Próximo resgate disponível em {format_time(segundos_restantes)}."
            )
            await message.edit(embed=embed)

        embed.title = "✅ Pronto para coletar!"
        embed.description = f"🎉 | {ctx.author.mention}, você já pode coletar suas luzes novamente!"
        embed.color = discord.Color.green()
        await message.edit(embed=embed)

@bot.command()
async def luz(ctx, user: discord.Member = None):
    """Comando para verificar quantas luzes um usuário tem."""
    # Se ninguém for mencionado, usa o próprio autor do comando
    user = user or ctx.author
    user_id = str(user.id)

    criar_usuario(user_id)  # Garante que o usuário está registrado
    user_data = db.get_user_data(user_id)
    luzes = user_data.get("luzes", 0)

    embed = discord.Embed(
        title="💡 Saldo de Luzes",
        description=f"{user.mention} tem **{luzes:,}** luzes! ✨",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    await ctx.send(embed=embed)

class RankingView(discord.ui.View):
    def __init__(self, ranking, is_local, page_size=10, timeout=60):
        super().__init__(timeout=timeout)
        self.ranking = ranking
        self.current_page = 0
        self.page_size = page_size
        self.total_pages = max(1, (len(ranking) - 1) // page_size + 1)
        self.is_local = is_local

        self.previous_button = discord.ui.Button(label="◀", style=discord.ButtonStyle.primary, disabled=True)
        self.next_button = discord.ui.Button(label="▶", style=discord.ButtonStyle.primary)

        self.previous_button.callback = self.previous_page
        self.next_button.callback = self.next_page

        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        self.update_buttons()

    def update_buttons(self):
        """ Atualiza o estado dos botões de navegação. """
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1

    async def update_message(self, interaction: discord.Interaction):
        """ Exibe a animação de 'digitando...' antes de atualizar o ranking. """

        # Ativa a animação de "digitando..."
        async with interaction.channel.typing():
            await asyncio.sleep(1.5)  # Delay para parecer natural

            self.update_buttons()
            await interaction.edit_original_response(embed=await self.get_embed(), view=self)

    async def previous_page(self, interaction: discord.Interaction):
        """ Retrocede uma página com animação. """
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_message(interaction)

    async def next_page(self, interaction: discord.Interaction):
        """ Avança uma página com animação. """
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        await self.update_message(interaction)

    async def get_embed(self):
        """ Gera o embed do ranking com base na página atual. """
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.ranking))
        current_page_items = self.ranking[start_idx:end_idx]

        embed = discord.Embed(
            title=f"Ranking de Luzes {'Local' if self.is_local else 'Global'}",
            description=f"| Página {self.current_page + 1}",
            color=discord.Color.green() if self.is_local else discord.Color.purple()
        )

        for i, (user_id, data) in enumerate(current_page_items, start=start_idx + 1):
            try:
                user = await bot.fetch_user(int(user_id))
                luzes = data.get("luzes", 0) if not self.is_local else data
                embed.add_field(name=f"{i}. {user.name}", value=f"{luzes} luzes", inline=False)

                if i == 1 and self.current_page == 0:
                    embed.set_thumbnail(url=user.display_avatar.url)
            except discord.NotFound:
                continue

        return embed

@bot.command()
async def rank(ctx, tipo: str = "luzes", page_size: int = 10):
    if page_size < 1:
        page_size = 1
    elif page_size > 25:
        page_size = 25

    tipo_parts = tipo.lower().split()
    tipo_principal = tipo_parts[0]

    async with ctx.typing():  # Ativa animação "digitando..."
        await asyncio.sleep(1.5)  # Pequeno delay para parecer natural

        if len(tipo_parts) > 1 and tipo_parts[1] == "local":
            if ctx.guild:
                ranking = sorted(
                    [(member.id, db.get_user_data(str(member.id)).get("luzes", 0))
                     for member in ctx.guild.members if db.get_user_data(str(member.id)).get("luzes", 0) > 0],
                    key=lambda x: x[1], reverse=True)

                if not ranking:
                    await ctx.send("Ainda não há dados suficientes para exibir o ranking local.")
                    return

                view = RankingView(ranking, is_local=True, page_size=page_size)
                await ctx.send(embed=await view.get_embed(), view=view)
            else:
                await ctx.send("Este comando está disponível apenas em servidores.")

        elif tipo_principal == "luzes":
            ranking = [(user_id, data) for user_id, data in db.data.items() if data.get("luzes", 0) > 0]
            ranking = sorted(ranking, key=lambda x: x[1].get("luzes", 0), reverse=True)

            if not ranking:
                await ctx.send("Ainda não há dados suficientes para exibir o ranking global.")
                return

            view = RankingView(ranking, is_local=False, page_size=page_size)
            await ctx.send(embed=await view.get_embed(), view=view)

        else:
            await ctx.send(f"{ctx.author.mention} Por favor, informe um tipo de ranking válido: `!rank luzes` ou `!rank luzes local`.")

@bot.command() 
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Comando para limpar mensagens em um canal. Requer permissão de gerenciar mensagens."""
    if amount < 2 or amount > 1000:
        await ctx.send(f"❌ | {ctx.author.mention} Eu só consigo limpar entre 2 até 1000 mensagens passadas!")
        return

    try:
        # Exclui as mensagens
        deleted = await ctx.channel.purge(limit=amount)

        # Verifica se nenhuma mensagem foi deletada
        if len(deleted) == 0:
            await ctx.send(
                f":error: | {ctx.author.mention} Não consegui encontrar nenhuma mensagem para ser deletada... "
                f"Eu não consigo deletar mensagens que foram enviadas há mais de duas semanas devido a limitações do Discord!"
            )
            return

        # Envia mensagem personalizada com detalhes
        await ctx.send(
            f"🎉 | {ctx.author.mention} O chat teve {len(deleted)} mensagens deletadas por {ctx.author.mention}!"
        )
    except Exception as e:
        # Mensagem de erro ficará no chat
        await ctx.send(f"❌ | Ocorreu um erro ao tentar limpar as mensagens: {e}")

@bot.command()
async def avatar(ctx, user: discord.User = None):
    """
    Comando para exibir o avatar de um usuário no estilo Loritta, mencionando com notificação.
    """
    user = user or ctx.author  # Se não houver menção, usa o autor do comando

    avatar_url = user.display_avatar.url  # Obtém o link do avatar

    # Criação do embed no estilo Loritta
    embed = discord.Embed(
        title=f"🖼️{user.name}",  # Título no embed
        color=discord.Color.blue()
    )

    embed.set_image(url=avatar_url)
    embed.set_footer(text="Apesar de tudo, ainda é você.")

    # Criando um botão para abrir o avatar no navegador
    view = discord.ui.View()
    button = discord.ui.Button(label="Abrir avatar no navegador", url=avatar_url)
    view.add_item(button)

    # Responde mencionando o autor do comando COM notificação
    await ctx.reply(embed=embed, view=view, mention_author=True)

@bot.command()
@commands.is_owner()
async def desligar(ctx):
    """Comando para desligar o bot (apenas para o dono)."""
    await ctx.send("Saindo do ar para manutenção... ")
    await bot.close()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ **Comando não encontrado, {ctx.author.mention}!**\nUse `!cmd` para ver a lista de comandos disponíveis.")
    else:
        # Caso algum erro diferente aconteça, mostre uma mensagem genérica.
        await ctx.send(f"⚠️ **Ocorreu um erro, {ctx.author.mention}. Por favor, tente novamente ou contate o administrador.**")
        # Opcional: log do erro no console
        print(f"Erro não tratado: {error}")

tarefas = {}  # Dicionário para armazenar tarefas por servidor (guild_id)

@bot.event
async def on_ready():
    print(f"{bot.user} está online em {len(bot.guilds)} servidores!")

def get_guild_tasks(guild_id):
    """Retorna a lista de tarefas do servidor ou inicializa se não existir."""
    return tarefas.setdefault(guild_id, [])

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", help="Exibe informações sobre um usuário.")
    async def userinfo(self, ctx, member: discord.Member = None):
        """Exibe informações detalhadas sobre um usuário."""
        if member is None:
            member = ctx.author  # Se ninguém for mencionado, usa quem chamou o comando

        # Cor baseada no cargo mais alto do usuário
        color = member.color if member.color != discord.Color.default() else discord.Color.blue()

        embed = discord.Embed(
            title=f"🌟 Informações de {member.name}",
            description=f"🔹 Aqui estão os detalhes sobre {member.mention}:",
            color=color
        )

        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        # Nome e ID do usuário
        embed.add_field(name="📌 **Nome de Usuário**", value=f"`{member.name}`", inline=True)
        embed.add_field(name="🆔 **ID do Usuário**", value=f"`{member.id}`", inline=True)

        # Datas formatadas
        embed.add_field(
            name="📅 **Conta Criada em**", 
            value=f"`{member.created_at.strftime('%d/%m/%Y')}`", 
            inline=False
        )
        if member.joined_at:
            embed.add_field(
                name="🏠 **Entrou no Servidor em**", 
                value=f"`{member.joined_at.strftime('%d/%m/%Y')}`", 
                inline=False
            )

        # Cargos organizados (do mais alto para o mais baixo, sem @everyone)
        roles = sorted(member.roles, key=lambda r: r.position, reverse=True)
        roles_text = "\n".join([f"🔹 {role.mention}" for role in roles if role.name != "@everyone"])
        embed.add_field(name="🎭 **Cargos**", value=roles_text if roles_text else "Nenhum", inline=False)

        # Rodapé personalizado
        embed.set_footer(text="📌 Informações extraídas com sucesso! | Luminarls")

        await ctx.send(embed=embed)

class InviteButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="🔗 Adicionar Luminarls",
            url="https://discord.com/oauth2/authorize?client_id=1351585153209597992&permissions=1153400515398839&integration_type=0&scope=bot",
            style=discord.ButtonStyle.link
        ))
        self.add_item(discord.ui.Button(
            label="adicione na sua conta",
            url="https://discord.com/oauth2/authorize?client_id=1351585153209597992",  # Substitua pelo link real do seu servidor de suporte
            style=discord.ButtonStyle.link
        ))

@bot.command()
async def rolar(ctx, minimo: int = 1, maximo: int = 100):
    if minimo >= maximo:
        await ctx.send("⚠️ O valor mínimo deve ser menor que o máximo!")
        return
    
    numero = random.randint(minimo, maximo)
    await ctx.send(f"🎲 {ctx.author.mention}, você rolou: **{numero}**!")

@bot.command(name="convite")  # Define o comando como "!convite"
async def convite(ctx):
    embed = discord.Embed(
        title="🌙 **Adicione Luminarls ao seu servidor!**",
        description="Melhore seu servidor com meus recursos avançados. Clique nos botões abaixo! 🚀",
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    embed.set_footer(text="Estou pronta para ajudar no seu servidor!", icon_url=ctx.bot.user.avatar.url)

    view = InviteButton()  # Instancia a view com os botões

    await ctx.send(embed=embed, view=view)  # Envia a embed com os botões

@bot.command(name="addluzes")
@commands.has_permissions(administrator=True)  # Restrito a administradores
async def addluzes(ctx, user: discord.Member = None, quantidade: int = None):
    """
    Comando para adicionar luzes a um usuário específico.
    Uso: !addluzes @usuário 100
    """
    if not user or not quantidade:
        await ctx.send("❌ | Comando incorreto. Use `!addluzes @usuário quantidade`")
        return

    if quantidade <= 0:
        await ctx.send("❌ | A quantidade de luzes deve ser um número positivo.")
        return

    user_id = str(user.id)
    criar_usuario(user_id)  # Garante que o usuário existe no banco de dados

    luzes_antes = db.get_user_data(user_id).get("luzes", 0)
    db.data[user_id]["luzes"] += quantidade
    db.save()

    embed = discord.Embed(
        title="💡 Luzes Adicionadas",
        description=f"✅ | {quantidade} luzes foram adicionadas para {user.mention}.\n💡 | **{luzes_antes}** → **{db.data[user_id]['luzes']}** luzes",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Ação executada por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# Função para criar um usuário no banco de dados se ele não existir
def criar_usuario(user_id):
    if user_id not in db.data:
        db.data[user_id] = {"luzes": 0}  # Adiciona o usuário com saldo de 0 Luzes
        db.save()

# Comando de transferência de luzes entre usuários com confirmação
@bot.command(name="pay", description="Transfira luzes para outro usuário.") 
async def pay(ctx, user: discord.Member, quantidade: int):
    """
    Comando para transferir luzes para outro usuário com confirmação.
    """
    # Verificação para evitar transferir para si mesmo ou para bots
    if user.id == ctx.author.id:
        await ctx.send("❌ Você não pode transferir luzes para si mesmo.")
        return

    if user.bot:
        await ctx.send("❌ Você não pode transferir luzes para bots.")
        return

    # Verificação se a quantidade é maior que 0
    if quantidade <= 0:
        await ctx.send("❌ A quantidade de luzes deve ser maior que 0.")
        return

    user_id = str(ctx.author.id)
    target_id = str(user.id)

    # Criar usuário se ele não existir
    criar_usuario(user_id)
    criar_usuario(target_id)

    saldo_atual = db.get_user_data(user_id).get("luzes", 0)

    # Verificação de saldo suficiente
    if saldo_atual < quantidade:
        await ctx.send(f"❌ Você não tem luzes suficientes. Seu saldo atual é de **{saldo_atual}** luzes.")
        return

    # Classe para confirmação da transação
    class ConfirmarTransacao(discord.ui.View):
        def __init__(self, sender, receiver, amount):
            super().__init__(timeout=60)  # Tempo limite ajustado para 1 minuto
            self.sender = sender
            self.receiver = receiver
            self.amount = amount

        @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.green)
        async def confirmar(self, interaction_confirm: discord.Interaction, button: discord.ui.Button):
            if interaction_confirm.user != self.receiver:
                await interaction_confirm.response.send_message("❌ Apenas o destinatário pode confirmar esta transação.", ephemeral=True)
                return

            # Realiza a transferência de luzes
            db.data[user_id]["luzes"] -= self.amount
            db.data[target_id]["luzes"] += self.amount
            db.save()

            # Cria o embed de sucesso
            embed = discord.Embed(
                title="💰 Transferência Concluída!",
                description=f"{self.sender.mention} transferiu **{self.amount}** luzes para {self.receiver.mention}.",
                color=discord.Color.green()
            )
            embed.add_field(name="Saldo Atual do Remetente", value=f"**{db.data[user_id]['luzes']}** luzes", inline=True)
            embed.add_field(name="Saldo Atual do Destinatário", value=f"**{db.data[target_id]['luzes']}** luzes", inline=True)
            await interaction_confirm.message.edit(embed=embed, view=None)
            self.stop()

        @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
        async def cancelar(self, interaction_cancel: discord.Interaction, button: discord.ui.Button):
            if interaction_cancel.user != self.receiver:
                await interaction_cancel.response.send_message("❌ Apenas o destinatário pode cancelar esta transação.", ephemeral=True)
                return

            embed = discord.Embed(
                title="❌ Transferência Cancelada",
                description=f"A transferência de **{self.amount}** luzes foi cancelada por {self.receiver.mention}.",
                color=discord.Color.red()
            )
            await interaction_cancel.message.edit(embed=embed, view=None)
            self.stop()

    # Cria o embed de confirmação de transferência
    embed = discord.Embed(
        title="💸 Confirmação de Transferência",
        description=f"{ctx.author.mention} deseja transferir **{quantidade}** luzes para {user.mention}.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="O destinatário tem 1 minuto para confirmar ou cancelar a transação.")

    # Cria a view para os botões
    view = ConfirmarTransacao(ctx.author, user, quantidade)

    # Menciona o destinatário para garantir que ele veja a mensagem
    await ctx.send(content=f"{user.mention}", embed=embed, view=view)

@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author  # Se nenhum usuário for mencionado, pega quem usou o comando

    embed = discord.Embed(title="Informações do Usuário", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="👤 Nome", value=member.name, inline=True)
    embed.add_field(name="🏷️ Apelido", value=member.nick if member.nick else "Nenhum", inline=True)
    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📅 Conta criada em", value=member.created_at.strftime("%d/%m/%Y às %H:%M"), inline=True)
    embed.add_field(name="📥 Entrou no servidor", value=member.joined_at.strftime("%d/%m/%Y às %H:%M"), inline=True)
    embed.add_field(name="🎭 Cargos", value=", ".join([role.mention for role in member.roles if role.name != "@everyone"]) or "Nenhum", inline=False)

    await ctx.send(embed=embed)
    
@bot.command()
@commands.is_owner()  # Apenas o dono do bot pode usar
async def servidores(ctx):
    guilds = sorted(bot.guilds, key=lambda g: g.name.lower())  # Ordena alfabeticamente
    servidores_lista = "\n".join([f"{i+1}. {guild.name} (ID: {guild.id})" for i, guild in enumerate(guilds)])
    
    if not servidores_lista:
        servidores_lista = "O bot não está em nenhum servidor."

    await ctx.send(f"🌍 O bot está nos seguintes servidores:\n```{servidores_lista}```")

@bot.command(name="coinflip", help="Cara ou coroa 🪙")
async def coinflip(ctx):
    resultado = random.choice(["Cara", "Coroa"])
    embed = discord.Embed(
        title="🪙 Coinflip!",
        description=f"O resultado foi **{resultado}**!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

quotes = [
    "A persistência realiza o impossível. ✨",
    "Acredite em você e tudo será possível! 🌟",
    "O sucesso é a soma de pequenos esforços repetidos diariamente. 💡",
    "A vida é feita de desafios, supere cada um deles! 🚀",
    "Nunca desista dos seus sonhos. ✨"
]

@bot.command(name="quote", help="Exibe uma citação aleatória. 💬")
async def quote(ctx):
    citacao = random.choice(quotes)
    embed = discord.Embed(
        title="💬 Citação Aleatória",
        description=f"📜 **{citacao}**",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def criarconvite(ctx, server_id: int):
    guild = bot.get_guild(server_id)
    if guild:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).create_instant_invite:
                invite = await channel.create_invite(max_uses=1, unique=True)
                await ctx.send(f"🎟️ Convite gerado: {invite.url}")
                return
    await ctx.send("❌ Não foi possível gerar um convite para esse servidor.")

piadas = [
    "Por que o livro de matemática estava triste? Porque tinha muitos problemas!",
    "O que o zero disse para o oito? Belo cinto!",
    "Qual é o animal mais antigo do mundo? A zebra, porque está em preto e branco!"
]

respostas_8ball = [
    "Sim!", "Não!", "Talvez...", "Definitivamente!", "Duvido muito...",
    "Com certeza!", "Melhor não contar com isso.", "As estrelas dizem que sim!"
]

@bot.command()
async def piada(ctx):
    await ctx.send(random.choice(piadas))


# Lista de respostas da 8ball
respostas_8ball = [
    "Sim.", "Não.", "Talvez.", "Com certeza!", "Definitivamente não.",
    "Pergunte novamente mais tarde.", "Não posso dizer agora.", "Provavelmente.",
    "Minhas fontes dizem que não.", "Sem dúvidas!", "Acho que sim.", "A resposta é incerta.",
    "Melhor não te dizer agora.", "Sinais apontam que sim.", "É duvidoso."
]

class OitoBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8ball", aliases=["oito_ball"], help="Faça uma pergunta e receba uma resposta da bola mágica 🎱")
    async def oito_ball(self, ctx, *, pergunta: str):
        """Comando da bola 8 mágica"""
        resposta = random.choice(respostas_8ball)
        embed = discord.Embed(
            title="🎱 Bola 8 Mágica",
            description=f"**Pergunta:** {pergunta}\n**Resposta:** {resposta}",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

@bot.command()
async def abraço(ctx, membro: discord.Member):
    respostas = [
        f"{ctx.author.mention} puxou {membro.mention} para um abraço tão forte que quase quebrou as costelas.",
        f"{ctx.author.mention} envolveu {membro.mention} em um abraço apertado que parecia um golpe de luta livre.",
        f"{membro.mention} foi pego de surpresa com um abraço esmagador de {ctx.author.mention}.",
        f"{ctx.author.mention} deu um abraço tão aconchegante em {membro.mention} que até o estresse do dia sumiu.",
        f"{membro.mention} tentou escapar, mas {ctx.author.mention} foi mais rápido e deu um abraço daqueles que marcam.",
        f"{ctx.author.mention} deu um abraço tão apertado em {membro.mention} que até o tempo parou por um instante.",
        f"{membro.mention} recebeu um abraço de {ctx.author.mention} e agora não quer mais soltar.",
        f"{ctx.author.mention} abraçou {membro.mention} com tanta força que deu até pra ouvir os ossos estalando.",
        f"{membro.mention} acabou de ganhar um abraço épico de {ctx.author.mention}, digno de filme.",
        f"{ctx.author.mention} viu {membro.mention} e nem pensou duas vezes antes de dar aquele abraço esmagador."
    ]

    await ctx.send(random.choice(respostas))

@bot.command()
async def beijo(ctx, membro: discord.Member):
    respostas = [
        f"{ctx.author.mention} deu um beijo estalado em {membro.mention}. O clima esquentou!",
        f"{ctx.author.mention} se aproximou e deu um beijo inesperado em {membro.mention}. Será que rolou química?",
        f"{membro.mention} foi surpreendido por um beijo repentino de {ctx.author.mention}. A galera ficou só de olho!",
        f"{ctx.author.mention} deu um beijo tão intenso em {membro.mention} que até as estrelas brilharam mais forte.",
        f"{membro.mention} recebeu um beijo de {ctx.author.mention} e ficou sem palavras. Isso vai dar o que falar!",
        f"{ctx.author.mention} se jogou e deu um beijo cinematográfico em {membro.mention}. Que cena!",
        f"{membro.mention} tentou escapar, mas {ctx.author.mention} foi mais rápido e tascou um beijo certeiro.",
        f"{ctx.author.mention} lançou aquele olhar e sem hesitar deu um beijo marcante em {membro.mention}.",
        f"{membro.mention} recebeu um beijo de {ctx.author.mention} e agora ficou todo bobo. O que será que vem depois?",
        f"{ctx.author.mention} tomou coragem e deu um beijo arrebatador em {membro.mention}. Que momento!"
    ]

    await ctx.send(random.choice(respostas))
    
@bot.command()
async def tapinha(ctx, membro: discord.Member):
    respostas = [
        f"{ctx.author.mention} deu um tapa tão forte em {membro.mention} que até o Wi-Fi dele caiu.",
        f"{membro.mention} levou um tapa de {ctx.author.mention} tão violento que até o Thanos ficou com inveja.",
        f"{ctx.author.mention} estalou a mão na cara de {membro.mention}, que agora tá vendo estrela até em 8K.",
        f"{membro.mention} foi parar na Lua depois de um tapa bem dado por {ctx.author.mention}.",
        f"O tapa que {ctx.author.mention} deu em {membro.mention} foi tão forte que até a avó do membro sentiu no além.",
        f"{ctx.author.mention} deu um tapão em {membro.mention} e o barulho foi tão alto que apareceu no Jornal Nacional.",
        f"{membro.mention} rodopiou três vezes no ar depois do tapão de {ctx.author.mention} e agora pensa que é Beyblade.",
        f"{ctx.author.mention} meteu um tapa tão absurdo em {membro.mention} que a física precisou ser reescrita.",
        f"{ctx.author.mention} deu um tapa em {membro.mention}, e o estrondo foi tão grande que virou trend no TikTok.",
        f"{membro.mention} foi lançado para a estratosfera após levar um tapão do {ctx.author.mention}. Boa viagem."
    ]

    await ctx.send(random.choice(respostas))

@bot.command()
async def chorar(ctx):
    gifs_choro = [
        "https://media.discordapp.net/attachments/1352073568900354119/1352376497473716266/baby-crying.png?ex=67ddca42&is=67dc78c2&hm=c483a8c6589783e3bc9a907a68752f5005b76493acd23e721d3ff651f9d7dc86&=&format=webp&quality=lossless",
        "https://media.discordapp.net/attachments/1352073568900354119/1352376398878081156/bC3BCeee.png?ex=67ddca2b&is=67dc78ab&hm=d0a07f295fcd49140137a11481076d6d9fae49875a654688b7d50e4d1bcd091b&=&format=webp&quality=lossless",
        "https://media.discordapp.net/attachments/1352073568900354119/1352376266019307661/ayu-nao.png?ex=67ddca0b&is=67dc788b&hm=da7a2b0f7b72b3149129e6713273486e1a2c14ca5de0490faaf706166ef631ec&=&format=webp&quality=lossless"
    ]
    await ctx.send(random.choice(gifs_choro))

@bot.command()
async def frase(ctx):
    frases = [
        "As pessoas veem o que você mostra, não o que você sente.",
        "Muitos te julgam pelo que ouviram, não pelo que realmente és.",
        "Aparências enganam, mas poucos se dão ao trabalho de olhar além.",
        "Antes de conhecerem sua história, já escreveram um final para ela.",
        "O mundo seria mais justo se as pessoas ouvissem antes de julgar.",
        "Nem todo sorriso esconde felicidade, nem toda lágrima significa fraqueza.",
        "Não permita que o julgamento alheio defina quem você é.",
        "Quem te conhece de verdade não precisa de explicações.",
        "A pressa em julgar faz com que muitos percam a chance de conhecer algo incrível.",
        "Muitos falam, poucos entendem, quase ninguém se importa."
    ]

    await ctx.send(random.choice(frases))  # Escolhe e envia uma frase aleatória

@bot.tree.command(name="luzes", description="Colete luzes a cada 5 minutos.")
async def luzes(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    agora = datetime.utcnow()
    criar_usuario(user_id)

    user_data = db.get_user_data(user_id)
    ultimo_resgate = datetime.strptime(user_data.get("last_claimed", "2000-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
    tempo_passado = agora - ultimo_resgate

    if tempo_passado >= TEMPO_ESPERA:
        luzes_coletadas = calcular_luzes(BASE_LUZES)
        user_data["luzes"] += luzes_coletadas
        user_data["last_claimed"] = agora.strftime("%Y-%m-%d %H:%M:%S")
        db.update_user_data(user_id, user_data)

        frases = [
            f"🎉 | {interaction.user.mention}, você coletou **{luzes_coletadas}** luzes!",
            f"✨ | {interaction.user.mention}, você encontrou **{luzes_coletadas}** luzes brilhantes!",
        ]

        embed = discord.Embed(
            title="✨ Luzes Coletadas! ✨",
            description=random.choice(frases),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    else:
        tempo_restante = TEMPO_ESPERA - tempo_passado
        minutos, segundos = divmod(int(tempo_restante.total_seconds()), 60)

        embed = discord.Embed(
            title="⏳ Tempo de Espera",
            description=f"⚠️ | {interaction.user.mention}, você poderá coletar em **{minutos}m {segundos}s**.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="luz", description="Veja quantas luzes você tem.")
async def luz(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    criar_usuario(user_id)
    user_data = db.get_user_data(user_id)
    luzes = user_data.get("luzes", 0)

    embed = discord.Embed(
        title="💡 Suas Luzes",
        description=f"{interaction.user.mention}, você tem **{luzes:,}** luzes! ✨",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

class RankView(discord.ui.View):
    def __init__(self, page, total_paginas, callback):
        super().__init__()
        self.page = page
        self.total_paginas = total_paginas
        self.callback = callback

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()

        if self.page > 1:
            self.add_item(AnteriorButton(self.page, self.callback))

        if self.page < self.total_paginas:
            self.add_item(ProximoButton(self.page, self.callback))

class AnteriorButton(discord.ui.Button):
    def __init__(self, page, callback):
        super().__init__(style=discord.ButtonStyle.primary, label="⬅ Anterior")
        self.page = page
        self.callback = callback

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.callback(self.page - 1)

class ProximoButton(discord.ui.Button):
    def __init__(self, page, callback):
        super().__init__(style=discord.ButtonStyle.primary, label="Próximo ➡")
        self.page = page
        self.callback = callback

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.callback(self.page + 1)

@bot.tree.command(name="rank", description="Veja o ranking de luzes global ou local.")
@app_commands.describe(tipo="Escolha entre ranking local ou global.")
@app_commands.choices(tipo=[
    app_commands.Choice(name="Global", value="global"),
    app_commands.Choice(name="Local", value="local"),
])
async def luzes_rank(interaction: discord.Interaction, tipo: app_commands.Choice[str]):
    await interaction.response.defer()  # Evita erro de tempo limite

    if tipo.value == "local":
        if not interaction.guild:
            return await interaction.followup.send("❌ Este comando só pode ser usado em servidores.")

        ranking = [
            (member.id, (db.get_user_data(str(member.id)) or {"luzes": 0})["luzes"])
            for member in interaction.guild.members
            if (db.get_user_data(str(member.id)) or {"luzes": 0})["luzes"] > 0
        ]
    else:
        ranking = [
            (user_id, data.get("luzes", 0))
            for user_id, data in db.data.items()
            if data.get("luzes", 0) > 0
        ]

    ranking.sort(key=lambda x: x[1], reverse=True)

    if not ranking:
        return await interaction.followup.send("😕 Ainda não há dados suficientes para exibir o ranking.")

    total_paginas = max(1, len(ranking) // 10 + (1 if len(ranking) % 10 > 0 else 0))

    class RankView(discord.ui.View):
        def __init__(self, page: int, mensagem: discord.Message, autor: discord.User):
            super().__init__()
            self.page = page
            self.mensagem = mensagem
            self.autor = autor

            self.previous = discord.ui.Button(label="◀️", style=discord.ButtonStyle.primary, disabled=True)
            self.next = discord.ui.Button(label="▶️", style=discord.ButtonStyle.primary)

            self.previous.callback = self.previous_page
            self.next.callback = self.next_page

            self.add_item(self.previous)
            self.add_item(self.next)

        async def update_page(self, primeira_pagina=False):
            if primeira_pagina:
                await self.mensagem.edit(content="Lumi está pensativa...")  # Apenas na primeira página

            start = (self.page - 1) * 10
            end = start + 10
            embed = discord.Embed(
                color=discord.Color.green() if tipo.value == "local" else discord.Color.purple()
            )

            ranking_parcial = ranking[start:end]
            if ranking_parcial:
                for i, (user_id, luzes) in enumerate(ranking_parcial, start=start + 1):
                    try:
                        user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
                        embed.add_field(name=f"{i}. {user.name}", value=f"**{luzes} luzes**", inline=False)
                    except:
                        continue
            else:
                embed.description = "😕 Não há jogadores suficientes para esta página."

            self.previous.disabled = self.page == 1
            self.next.disabled = self.page >= total_paginas

            await self.mensagem.edit(content=f"| Página {self.page}", embed=embed, view=self)

        async def previous_page(self, interaction: discord.Interaction):
            if interaction.user != self.autor:
                return await interaction.response.send_message("❌ Apenas o autor do comando pode usar os botões.", ephemeral=True)

            self.page -= 1
            await self.update_page()

        async def next_page(self, interaction: discord.Interaction):
            if interaction.user != self.autor:
                return await interaction.response.send_message("❌ Apenas o autor do comando pode usar os botões.", ephemeral=True)

            self.page += 1
            await self.update_page()

    mensagem = await interaction.followup.send("Lumi está pensativa...")
    view = RankView(1, mensagem, interaction.user)
    await view.update_page(primeira_pagina=True)

@bot.tree.command(name="rolar", description="Gere um número aleatório entre dois valores.")
async def rolar(interaction: discord.Interaction, minimo: int = 1, maximo: int = 100):
    if minimo > maximo:
        await interaction.response.send_message("⚠️ O valor mínimo não pode ser maior que o máximo!", ephemeral=True)
        return

    numero_sorteado = random.randint(minimo, maximo)

    embed = discord.Embed(
        title="🎲 Número Aleatório 🎲",
        description=f"{interaction.user.mention}, o número sorteado foi **{numero_sorteado}**!",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="Transfira luzes para outro usuário.")
@app_commands.describe(user="Usuário para quem você deseja transferir luzes", quantidade="Quantidade de luzes a transferir")
async def pay(interaction: discord.Interaction, user: discord.Member, quantidade: int):
    """
    Comando para transferir luzes para outro usuário com confirmação.
    """
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ Você não pode transferir luzes para si mesmo.", ephemeral=True)
        return

    if user.bot:
        await interaction.response.send_message("❌ Você não pode transferir luzes para bots.", ephemeral=True)
        return

    if quantidade <= 0:
        await interaction.response.send_message("❌ A quantidade de luzes deve ser maior que 0.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    target_id = str(user.id)

    criar_usuario(user_id)
    criar_usuario(target_id)

    saldo_atual = db.get_user_data(user_id).get("luzes", 0)

    if saldo_atual < quantidade:
        await interaction.response.send_message(f"❌ Você não tem luzes suficientes. Seu saldo atual é de **{saldo_atual}** luzes.", ephemeral=True)
        return

    class ConfirmarTransacao(discord.ui.View):
        def __init__(self, sender, receiver, amount):
            super().__init__(timeout=60)  # Tempo limite ajustado para 1 minuto (60 segundos)
            self.sender = sender
            self.receiver = receiver
            self.amount = amount
            self.value = None

        @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.green)
        async def confirmar(self, interaction_confirm: discord.Interaction, button: discord.ui.Button):
            if interaction_confirm.user != self.receiver:
                await interaction_confirm.response.send_message("❌ Apenas o destinatário pode confirmar esta transação.", ephemeral=True)
                return

            db.data[user_id]["luzes"] -= self.amount
            db.data[target_id]["luzes"] += self.amount
            db.save()

            embed = discord.Embed(
                title="💰 Transferência Concluída!",
                description=f"{self.sender.mention} transferiu **{self.amount}** luzes para {self.receiver.mention}.",
                color=discord.Color.green()
            )
            embed.add_field(name="Saldo Atual do Remetente", value=f"**{db.data[user_id]['luzes']}** luzes", inline=True)
            embed.add_field(name="Saldo Atual do Destinatário", value=f"**{db.data[target_id]['luzes']}** luzes", inline=True)
            await interaction_confirm.message.edit(embed=embed, view=None)
            self.stop()

        @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
        async def cancelar(self, interaction_cancel: discord.Interaction, button: discord.ui.Button):
            if interaction_cancel.user != self.receiver:
                await interaction_cancel.response.send_message("❌ Apenas o destinatário pode cancelar esta transação.", ephemeral=True)
                return

            embed = discord.Embed(
                title="❌ Transferência Cancelada",
                description=f"A transferência de **{self.amount}** luzes foi cancelada por {self.receiver.mention}.",
                color=discord.Color.red()
            )
            await interaction_cancel.message.edit(embed=embed, view=None)
            self.stop()

    embed = discord.Embed(
        title="💸 Confirmação de Transferência",
        description=f"{interaction.user.mention} deseja transferir **{quantidade}** luzes para {user.mention}.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="O destinatário tem 1 minuto para confirmar ou cancelar a transação.")

    view = ConfirmarTransacao(interaction.user, user, quantidade)

    # Menciona o destinatário fora do embed para garantir a notificação
    await interaction.response.send_message(content=f"{user.mention}", embed=embed, view=view)
    
class AjudaView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id  # Guarda o ID de quem executou o comando
        self.add_item(AjudaSelect(author_id))

class AjudaSelect(Select):
    def __init__(self, author_id: int):
        self.author_id = author_id
        
        options = [
            discord.SelectOption(label="Diversão", description="Veja comandos de diversão 🎉", emoji="🎭"),
            discord.SelectOption(label="Utilidade", description="Comandos úteis para o dia a dia 🛠️", emoji="🔧"),
            discord.SelectOption(label="Economia", description="Comandos relacionados à economia 💰", emoji="💰"),
            discord.SelectOption(label="Voltar ao Início", description="Retornar ao menu principal 🔙", emoji="↩️"),
        ]
        
        super().__init__(placeholder="Selecione uma categoria:", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Você não pode interagir com este menu!", ephemeral=True)
            return

        categoria = self.values[0]
        embed = discord.Embed(color=discord.Color.blurple())

        if categoria == "Diversão":
            embed.title = "🎭 Comandos de Diversão"
            embed.description = (
                "`!rolar` - `/rolar` - Rola um dado\n"
                "`!coinflip` - Cara ou coroa\n"
                "`!abraço` - Envie um abraço para alguém 🤗\n"
                "`!beijo` - Dê um beijo em alguém 💋\n"
                "`!tapinha` - Dê um tapinha em alguém ✋\n"
                "`!chorar` - Demonstre sua tristeza 😢\n"
                "`!frase` - Receba uma frase aleatória 📜"
            )

        elif categoria == "Utilidade":
            embed.title = "🔧 Comandos de Utilidade"
            embed.description = (
                "`!ping`- Mostra a latência\n"
                "`!avatar` - Exibe o avatar de um usuário\n"
                "`!convite` - Link do bot"
            )

        elif categoria == "Economia":
            embed.title = "💰 Comandos de Economia"
            embed.description = (
                "`!luzes` - `/luzes` - Veja quantas luzes você tem\n"
                "`!rank` - `/rank` - Veja o ranking de luzes"
            )

        elif categoria == "Voltar ao Início":
            embed.title = "📜 Menu de Ajuda"
            embed.description = "Escolha uma categoria no menu abaixo para ver os comandos."

        await interaction.response.edit_message(embed=embed, view=self.view)

class AjudaView(View):
    def __init__(self, author_id: int):
        super().__init__()
        self.add_item(AjudaSelect(author_id))

@bot.tree.command(name="luzguia", description="Mostra a central de comandos do bot.")
async def luzguia(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Ajuda da Luminarls",
        description=(
            "💡 **A Luminarls é um bot de economia, diversão e utilidades!**\n\n"
            "Selecione uma categoria abaixo para ver os comandos disponíveis."
        ),
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url=interaction.client.user.display_avatar.url)  # Avatar do bot

    await interaction.response.send_message(embed=embed, view=AjudaView(interaction.user.id))

@bot.tree.command(name="ping", description="Mostra a latência do bot em tempo real")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()  # Evita timeout e indica que o bot está processando

    shard_id = interaction.guild.shard_id if interaction.guild else 0  # Obtém a shard do servidor
    total_shards = bot.shard_count if bot.shard_count else 1  # Número total de shards
    cluster_name = "Luminarls Cluster"  # Nome do cluster do bot
    gateway_ping = round(bot.latency * 1000)  # Ping do gateway

    # Marca o tempo de início
    start_time = time.perf_counter()
    message = await interaction.followup.send("🏓 Calculando latência...")  # Envia mensagem temporária
    api_ping = round((time.perf_counter() - start_time) * 1000)  # Calcula o tempo de resposta da API

    # Cria o embed com os valores finais
    embed = discord.Embed(color=discord.Color.purple())
    embed.add_field(
        name="🏓 | Pong!", 
        value=f"📡 Shard {shard_id}/{total_shards} - {cluster_name}",
        inline=False
    )
    embed.add_field(name="⏱ | Gateway Ping", value=f"{gateway_ping}ms", inline=False)
    embed.add_field(name="⚡ | API Ping", value=f"{api_ping}ms", inline=False)

    # Edita a mensagem inicial com o embed final
    await message.edit(content=None, embed=embed)

@bot.tree.command(name="infolumi", description="Veja informações sobre a Luminarls!")
async def infolumi(interaction: discord.Interaction):
    total_servidores = len(bot.guilds)
    total_comandos = len(bot.tree.get_commands())

    embed = discord.Embed(
        title="🌙 Oi! Eu sou a Lumináris!",
        description=(
            f"Eu estou atualmente em **{total_servidores} servidores** e tenho **{total_comandos} comandos**.\n"
            "Fui criada para tornar seus servidores mais **divertidos e inteligentes**!\n\n"
            "Eu fui programada em **Python** usando **discord.py** e me mantenho online com a **hospedagem do Visual studio**.\n\n"
            "💜 Desenvolvida por `crazy`"
        ),
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1351585153209597992/1012446b215e303ec69f72a40863ab4b.png?size=2048")
    embed.add_field(name="🔗 Me adicione", value="[Clique aqui](https://discord.com/oauth2/authorize?client_id=1351585153209597992&permissions=1134699690920119&integration_type=0&scope=bot)", inline=True)
    embed.add_field(name="🛠 Servidor de Suporte", value="[Entre aqui](https://discord.gg/dYrZdRcHsb)", inline=True)

    await interaction.response.send_message(embed=embed)

class VerImagem(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        self.add_item(discord.ui.Button(label="🔗 Abrir no navegador", url=url, style=discord.ButtonStyle.link))

@bot.tree.command(name="avatarver", description="Exibe o avatar de um usuário.")  # Nome atualizado
@app_commands.describe(user="Usuário para ver o avatar (opcional)")
async def avatarver(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user  
    avatar_url = user.display_avatar.url

    embed = discord.Embed(
        title=f"🖼️ {user.display_name}",
        color=discord.Color.blue()
    )
    embed.set_image(url=avatar_url)

    await interaction.response.send_message(embed=embed, view=VerImagem(avatar_url))  # Adicionando a view

# Comando /banner
@bot.tree.command(name="banner", description="Exibe o banner de um usuário.")
@app_commands.describe(user="Usuário para ver o banner (opcional)")
async def banner(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    
    user_data = await bot.fetch_user(user.id)
    banner_url = user_data.banner.url if user_data.banner else None

    if banner_url:
        embed = discord.Embed(
            title=f"🎨{user.display_name}",
            color=discord.Color.blue()
        )
        embed.set_image(url=banner_url)

        await interaction.response.send_message(embed=embed, view=VerImagem(banner_url))
    else:
        await interaction.response.send_message(f"❌ {user.mention} não possui um banner definido.", ephemeral=True)

@bot.event
async def on_ready():
    await bot.wait_until_ready()  
    print(f"🚀 {bot.user.name} está online e pronto para uso!")

    # Sincroniza os comandos slash automaticamente ao iniciar
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash Commands sincronizados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao sincronizar Slash Commands: {e}")

# Inicia o bot com o token
bot.run(TOKEN)
