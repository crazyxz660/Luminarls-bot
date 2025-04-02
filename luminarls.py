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
from PIL import Image, ImageDraw, ImageFont
import io

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

    embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/pWZE0gVVSQjJBRz7FllilfKkAo-v8AOCCy9NUdFCa6w/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/1351585153209597992/a0c671f9c2819ef8511c843e1ee9b947.png?format=webp&quality=lossless&width=667&height=667")

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
        # Inicia a animação de digitação enquanto o bot processa a limpeza
        async with ctx.typing():  
            # Exclui as mensagens
            deleted = await ctx.channel.purge(limit=amount)
        
        # Mensagem final após a limpeza
        if len(deleted) == 0:
            await ctx.send(f"❌ | {ctx.author.mention} Não consegui encontrar mensagens para apagar.")
        else:
            await ctx.send(f"✅ | {ctx.author.mention} O chat teve {len(deleted)} mensagens deletadas!")

    except Exception as e:
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

# Função para carregar o XP do arquivo JSON
def carregar_xp():
    try:
        # Tenta abrir o arquivo e carregar os dados
        with open("dados_xp.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Se o arquivo não for encontrado, retorna um dicionário vazio
        return {}

# Função para salvar o XP no arquivo JSON
def salvar_xp(dados):
    # Abre o arquivo JSON para salvar os dados
    with open("dados_xp.json", "w") as f:
        json.dump(dados, f, indent=4)

# Função para gerar o embed com os dados da página
async def gerar_embed(pagina, ranking, itens_por_pagina, total_paginas):
    start_index = (pagina - 1) * itens_por_pagina
    end_index = start_index + itens_por_pagina
    embed = discord.Embed(title=f" Rank de XP - Página {pagina}/{total_paginas}", color=discord.Color.gold())

    # Adiciona os usuários da página atual ao embed
    for idx, (user_id, dados) in enumerate(ranking[start_index:end_index]):
        user = await bot.fetch_user(user_id)
        embed.add_field(name=f"{start_index + idx + 1}. {user.name}", value=f"XP: {dados['xp']} - Nível: {dados['nivel']}", inline=False)
    
    return embed

@bot.command()
async def rankxp(ctx, pagina: int = 1):
    # Carrega os dados de XP
    xp_usuarios = carregar_xp()

    # Ordena o ranking corretamente (maior nível e XP primeiro)
    ranking = sorted(xp_usuarios.items(), key=lambda x: (-x[1]["nivel"], -x[1]["xp"], x[0]))

    # Define a quantidade de itens por página (5 em 5)
    itens_por_pagina = 5
    total_paginas = (len(ranking) // itens_por_pagina) + (1 if len(ranking) % itens_por_pagina > 0 else 0)

    # Garante que a página solicitada não ultrapasse o total de páginas
    pagina = max(1, min(pagina, total_paginas))

    # Função para gerar o embed do ranking
    async def gerar_embed(pagina):
        start_index = (pagina - 1) * itens_por_pagina
        end_index = start_index + itens_por_pagina
        embed = discord.Embed(title="Rank de XP", color=discord.Color.gold())

        # Adiciona os usuários da página atual ao embed
        for idx, (user_id, dados) in enumerate(ranking[start_index:end_index], start=start_index + 1):
            user = await bot.fetch_user(user_id)
            embed.add_field(name=f"{idx}. {user.name}", value=f"XP: {dados['xp']} - Nível: {dados['nivel']}", inline=False)

        embed.set_footer(text=f"Página {pagina}/{total_paginas}")
        return embed

    # Criação dos botões de navegação
    class RankingView(discord.ui.View):
        def __init__(self, pagina_atual):
            super().__init__(timeout=300)  # Agora os botões duram 5 minutos
            self.pagina_atual = pagina_atual

        @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.primary)
        async def pagina_anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()  # Confirma a interação para evitar falha
            if self.pagina_atual > 1:
                self.pagina_atual -= 1
                embed = await gerar_embed(self.pagina_atual)
                view = RankingView(self.pagina_atual)  # Recria a view para estender o tempo de expiração
                await interaction.message.edit(embed=embed, view=view)

        @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.primary)
        async def proxima_pagina(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()  # Confirma a interação para evitar falha
            if self.pagina_atual < total_paginas:
                self.pagina_atual += 1
                embed = await gerar_embed(self.pagina_atual)
                view = RankingView(self.pagina_atual)  # Recria a view para estender o tempo de expiração
                await interaction.message.edit(embed=embed, view=view)

    # Envia a mensagem com o ranking e os botões
    embed = await gerar_embed(pagina)
    await ctx.send(embed=embed, view=RankingView(pagina))
    
# Função para salvar XP (substituir por banco de dados real)
def salvar_xp(dados):
    with open("dados_xp.json", "w") as f:
        json.dump(dados, f, indent=4)

xp_usuarios = carregar_xp()

# Função para gerar a barra de XP corretamente
def gerar_barra_xp(xp_atual, xp_necessario, largura=300, altura=20):
    """ Gera uma barra de XP proporcional ao progresso do usuário. """
    barra = Image.new("RGB", (largura, altura), color=(40, 40, 40))
    draw = ImageDraw.Draw(barra)

    # Evita que a barra ultrapasse 100%
    xp_porcentagem = min(1, xp_atual / xp_necessario)
    largura_barra = int(largura * xp_porcentagem)

    # Desenha a barra preenchida
    draw.rectangle([(0, 0), (largura_barra, altura)], fill=(0, 255, 0))
    
    return barra

# Evento de mensagem para adicionar XP
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    
    if user_id not in xp_usuarios:
        xp_usuarios[user_id] = {"xp": 0, "nivel": 1}

    xp_ganho = random.randint(5, 15)  # XP aleatório por mensagem
    xp_usuarios[user_id]["xp"] += xp_ganho
    xp_necessario = xp_usuarios[user_id]["nivel"] * 100

    if xp_usuarios[user_id]["xp"] >= xp_necessario:
        xp_usuarios[user_id]["xp"] -= xp_necessario
        xp_usuarios[user_id]["nivel"] += 1
        await message.channel.send(f"🎉 {message.author.mention} subiu para o nível {xp_usuarios[user_id]['nivel']}!")

    salvar_xp(xp_usuarios)
    await bot.process_commands(message)

# Comando !xp para exibir XP com barra visual
@bot.command()
async def xp(ctx):
    user_id = str(ctx.author.id)
    if user_id not in xp_usuarios:
        xp_usuarios[user_id] = {"xp": 0, "nivel": 1}

    xp_atual = xp_usuarios[user_id]["xp"]
    nivel_atual = xp_usuarios[user_id]["nivel"]
    xp_necessario = nivel_atual * 100

    # Gera a barra de XP corretamente
    barra_xp = gerar_barra_xp(xp_atual, xp_necessario)
    barra_xp_bytes = io.BytesIO()
    barra_xp.save(barra_xp_bytes, format="PNG")
    barra_xp_bytes.seek(0)

    embed = discord.Embed(
        title=f"{ctx.author.name} - Nível {nivel_atual}",
        description=f"XP: {xp_atual}/{xp_necessario}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=ctx.author.avatar.url)

    barra_xp_img = discord.File(barra_xp_bytes, filename="barra_xp.png")
    embed.set_image(url="attachment://barra_xp.png")

    await ctx.send(file=barra_xp_img, embed=embed)

# Variável que armazena o tempo de execução
start_time = time.time()

@bot.command()
async def uptime(ctx):
    # Calcula o tempo de execução
    uptime = time.time() - start_time
    # Converte o tempo para um formato legível
    uptime_timedelta = str(timedelta(seconds=int(uptime)))
    
    # Formatação para o formato brasileiro
    days, remainder = divmod(int(uptime), 86400)  # 86400 segundos = 1 dia
    hours, remainder = divmod(remainder, 3600)    # 3600 segundos = 1 hora
    minutes, seconds = divmod(remainder, 60)      # 60 segundos = 1 minuto
    
    # Cria a mensagem de resposta
    uptime_message = f"O bot está online há: "
    
    if days > 0:
        uptime_message += f"{days} dia(s), "
    if hours > 0:
        uptime_message += f"{hours} hora(s), "
    if minutes > 0:
        uptime_message += f"{minutes} minuto(s), "
    
    uptime_message += f"{seconds} segundo(s)."
    
    await ctx.send(uptime_message)

# Lista para armazenar os usuários que receberão o lembrete
votantes = set()

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')
    enviar_votacao.start()  # Inicia a tarefa de envio automático a cada 12h

@tasks.loop(hours=12)
async def enviar_votacao():
    """Envia lembretes de votação via DM para os usuários registrados."""
    for user_id in votantes:
        try:
            user = await bot.fetch_user(user_id)  # Obtém o usuário mesmo se não estiver na cache
            embed = discord.Embed(
                title="🌟 Vote no Luminarls!",
                description="Ajude o Luminarls a crescer votando nele no Top.gg! Cada voto faz a diferença! 💜",
                url="https://top.gg/bot/1351585153209597992/vote",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Você pode votar a cada 12 horas.")

            await user.send(embed=embed)

        except discord.Forbidden:
            print(f"Não foi possível enviar DM para {user.name} ({user.id}).")
        
        await asyncio.sleep(1)  # Pequeno delay para evitar rate limit

@bot.command()
async def registrar(ctx):
    """Comando para registrar o usuário para receber lembretes de votação."""
    if ctx.author.id in votantes:
        await ctx.send(f"{ctx.author.mention}, você já está registrado para receber lembretes! 💜")
    else:
        votantes.add(ctx.author.id)
        await ctx.send(f"{ctx.author.mention}, agora você receberá lembretes de votação na DM! 💜")

class InviteButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="🔗 Adicionar Luminarls",
            url="https://discord.com/oauth2/authorize?client_id=1351585153209597992&permissions=2147551239&integration_type=0&scope=bot",
            style=discord.ButtonStyle.link
        ))
        self.add_item(discord.ui.Button(
            label="adicione na sua conta",
            url="https://discord.com/oauth2/authorize?client_id=1351585153209597992",  # Substitua pelo link real do seu servidor de suporte
            style=discord.ButtonStyle.link
        ))

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

@bot.command()
async def rolar(ctx, minimo: int = 1, maximo: int = 100):
    if minimo >= maximo:
        await ctx.send("⚠️ O valor mínimo deve ser menor que o máximo!")
        return
    
    numero = random.randint(minimo, maximo)
    await ctx.send(f"🎲 {ctx.author.mention}, você rolou: **{numero}**!")

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
    embed.add_field(name=" Nome:", value=member.name, inline=True)
    embed.add_field(name=" Apelido:", value=member.nick if member.nick else "Nenhum", inline=True)
    embed.add_field(name=" ID:", value=member.id, inline=False)

    # Conta criada em com formato relativo
    embed.add_field(
        name=" Conta criada em:",
        value=f"<t:{int(member.created_at.timestamp())}:R>",
        inline=True
    )

    # Entrou no servidor com formato relativo
    embed.add_field(
        name=" Entrou no servidor:",
        value=f"<t:{int(member.joined_at.timestamp())}:R>",
        inline=True
    )

    # Exibindo os cargos
    embed.add_field(name=" Cargos:", value=", ".join([role.mention for role in member.roles if role.name != "@everyone"]) or "Nenhum", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="servericon", help="Mostra o ícone do servidor")
async def servericon(ctx):
    guild = ctx.guild
    embed = discord.Embed(color=discord.Color.green())  # Sem título
    embed.set_image(url=guild.icon.url)  # Adiciona o ícone do servidor

    # Criando o botão que abre o ícone no navegador
    button = Button(label="Abrir no navegador", url=guild.icon.url)  # Botão com link para o ícone

    # Criando a view e adicionando o botão
    view = View()
    view.add_item(button)
    
    # Enviar menção ao usuário que executou o comando e o embed com o ícone
    await ctx.reply(embed=embed, view=view, mention_author=True)

@bot.command(name="lock", help="Bloqueia o canal atual para impedir mensagens.")
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(" Este canal foi bloqueado. Apenas membros com permissões adequadas podem enviar mensagens.")

@bot.command(name="unlock", help="Desbloqueia o canal atual para permitir mensagens.")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("Este canal foi desbloqueado. Os membros agora podem enviar mensagens normalmente.")

@bot.command()
@commands.is_owner()  # Apenas o dono do bot pode usar este comando
async def sair(ctx, guild_id: int = None):
    if guild_id is None:
        return await ctx.send("❌ Você precisa fornecer o ID do servidor!")

    guild = bot.get_guild(guild_id)
    
    if guild is None:
        return await ctx.send("❌ O bot não está em um servidor com esse ID!")

    await guild.leave()
    await ctx.send(f"✅ O bot saiu do servidor **{guild.name}** ({guild.id}).")

@bot.command(name="addrole", help="Adiciona um cargo a um usuário.")
@commands.has_permissions(manage_roles=True)  # Apenas quem pode gerenciar cargos
async def addrole(ctx, user: discord.Member, role: discord.Role):
    await user.add_roles(role)
    await ctx.send(f"O cargo {role.name} foi adicionado a {user.mention}.")

@bot.command(name="removerole", help="Remove um cargo de um usuário.")
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, user: discord.Member, role: discord.Role):
    await user.remove_roles(role)
    await ctx.send(f"O cargo {role.name} foi removido de {user.mention}.")

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild

    # Tentando obter o dono do servidor
    owner = guild.owner
    if owner is None:  # Se não estiver carregado, busca pelo ID
        owner = await bot.fetch_user(guild.owner_id)

    owner_name = owner.mention if owner else "-"

    # Criando o embed
    embed = discord.Embed(title="Informações do Servidor", color=discord.Colour.random())
    embed.add_field(name="Nome do Servidor", value=guild.name, inline=True)
    embed.add_field(name="ID do Servidor", value=guild.id, inline=True)
    embed.add_field(name="Dono do Servidor", value=owner_name, inline=True)
    embed.add_field(name="Canais de Texto", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Canais de Voz", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="Funções", value=len(guild.roles), inline=True)
    embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)

    # Verifica se há um ícone antes de definir
    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)

    # Verifica se o autor tem um avatar antes de definir
    embed.set_footer(text=f'{ctx.author.name}', icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()  # Apenas o dono do bot pode usar
async def servidores(ctx):
    guilds = sorted(bot.guilds, key=lambda g: g.name.lower())  # Ordena alfabeticamente
    servidores_lista = "\n".join([f"{i+1}. {guild.name} (ID: {guild.id})" for i, guild in enumerate(guilds)])
    
    if not servidores_lista:
        servidores_lista = "O bot não está em nenhum servidor."

    await ctx.send(f"O bot está nos seguintes servidores:\n```{servidores_lista}```")

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

class AbraçoView(discord.ui.View):
    def __init__(self, autor, membro, gif_url):
        super().__init__(timeout=600)  # Botões ativos por 10 minutos
        self.autor = autor
        self.membro = membro
        self.gif_url = gif_url

    @discord.ui.button(label="💞 Retribuir", style=discord.ButtonStyle.primary)
    async def retribuir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            await interaction.response.send_message("❌ Apenas quem recebeu o abraço pode retribuir!", ephemeral=True)
            return

        respostas_retribuir = [
            f"{self.membro.mention} retribuiu o abraço com ainda mais força para {self.autor.mention}!",
            f"{self.membro.mention} se emocionou e abraçou {self.autor.mention} de volta com carinho!",
            f"{self.membro.mention} sorriu e retribuiu o abraço apertado de {self.autor.mention}.",
            f"{self.membro.mention} não resistiu e pulou nos braços de {self.autor.mention} para um abraço duplo!",
            f"{self.membro.mention} deu um abraço carinhoso e disse: 'Eu precisava disso!'",
            f"{self.membro.mention} sorriu e abraçou {self.autor.mention} novamente, sem querer soltar.",
            f"{self.membro.mention} apertou {self.autor.mention} forte e disse: 'Agora somos inseparáveis!'.",
            f"{self.membro.mention} se jogou nos braços de {self.autor.mention} para um abraço infinito!",
            f"{self.membro.mention} segurou {self.autor.mention} e disse: 'Abraços são a melhor coisa do mundo!'.",
            f"{self.membro.mention} retribuiu com um abraço tão forte que quase levantou {self.autor.mention} do chão!"
        ]

        gifs_retribuir = [
            "https://i.pinimg.com/originals/a6/e6/5a/a6e65ab98fc036a0f4bb677338abd6a9.gif",
            "https://i.pinimg.com/originals/7c/e6/c4/7ce6c444c0d69791db863a448132c9ed.gif",
            "https://i.pinimg.com/originals/95/19/2b/95192bdb70eb7e581db3e9af2032eac6.gif",
            "https://media1.tenor.com/m/HBTbcCNvLRIAAAAd/syno-i-love-you-syno.gif",
            "https://media1.tenor.com/m/JzxgF3aebL0AAAAd/hug-hugging.gif",
            "https://images-ext-1.discordapp.net/external/qlEeArkWM-N5IG7C3Mj4N76aPu8ZrhgK0ROCX9DHBYA/https/rrp-production.loritta.website/img/787b6a3578af65f05ec020fbf0f8639b3f8aabe1.gif",
            "https://images-ext-1.discordapp.net/external/jgvyV5hePHBZXXrfH_7MOUsSjcF5YmDOvVKtApE_IDE/https/rrp-production.loritta.website/img/f197272db0a82ef09fa62d5a7677b8fe6ed5c94e.gif",
            "https://images-ext-1.discordapp.net/external/M363yE5hOiBQVE5TpqzbUoquHu6-y3tVqH-6d9FYAUg/https/rrp-production.loritta.website/img/d271b0edb28f6f83817694713ddff056b704a237.gif",
            "https://images-ext-1.discordapp.net/external/5aEMYjfkAp69ij8IGKirqy9JVBjATqrqoBeHHCgYR9s/https/rrp-production.loritta.website/img/b9066b344edc3a417a99e0a7c51f84b6faf689d2.gif",
            "https://images-ext-1.discordapp.net/external/ZZTOpA2x33uOtoVOFKg77qvRa63WO81X-AKwk6xVfVI/https/rrp-production.loritta.website/img/4ade7b436d9663ad902ad8beb1c0e376fbb62f81.gif"
        ]

        gif_retribuir_url = random.choice(gifs_retribuir)

        embed = discord.Embed(
            description=random.choice(respostas_retribuir),
            color=discord.Color.purple()
        )
        embed.set_image(url=gif_retribuir_url)

        view = AbraçoView(self.membro, self.autor, gif_retribuir_url)  # Criar nova View para retribuir
        await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label="🖼️ Fonte da Imagem", style=discord.ButtonStyle.secondary)
    async def fonte_imagem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🔗 **Fonte do GIF:** [Clique aqui]({self.gif_url})", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # Desativa os botões quando expirar
        await self.message.edit(view=self)

@bot.command()
async def abraço(ctx, membro: discord.Member):
    respostas = [
        f"{ctx.author.mention} puxou {membro.mention} para um abraço tão forte que quase quebrou as costelas.",
        f"{ctx.author.mention} envolveu {membro.mention} em um abraço apertado que parecia um golpe de luta livre.",
        f"{membro.mention} foi pego de surpresa com um abraço esmagador de {ctx.author.mention}.",
        f"{ctx.author.mention} deu um abraço tão aconchegante em {membro.mention} que até o estresse do dia sumiu.",
        f"{ctx.author.mention} abriu os braços e {membro.mention} correu para um abraço apertado!",
        f"{ctx.author.mention} pegou {membro.mention} no colo e girou no ar antes de um grande abraço!",
        f"{ctx.author.mention} deu um abraço surpresa em {membro.mention}, que ficou sem palavras!",
        f"{ctx.author.mention} correu e pulou nos braços de {membro.mention} para um abraço incrível!",
        f"{ctx.author.mention} envolveu {membro.mention} em um abraço tão apertado que parecia um cobertor quente!",
        f"{ctx.author.mention} e {membro.mention} compartilharam um abraço tão sincero que emocionou a todos!"
    ]
    
    gifs_abraço = [
        "https://i.pinimg.com/originals/16/f4/ef/16f4ef8659534c88264670265e2a1626.gif",
        "https://i.pinimg.com/originals/08/22/44/0822444579b6859cd5179c509fe02241.gif",
        "https://images-ext-1.discordapp.net/external/8ojBvtJ_k7vXG9htJt-Kwds237ZGPfHDIw9sYktWYV4/https/rrp-production.loritta.website/img/246e077b2cdc962f2074c46d4ec5724dba74bbea.gif",
        "https://i.pinimg.com/originals/be/8d/41/be8d41333e616efab00959dde69ae8f0.gif",
        "https://i.pinimg.com/originals/10/32/cf/1032cf596158d5bda6cf35aef66e298c.gif",
        "https://i.pinimg.com/originals/89/7d/6b/897d6b583ea58239b85ddf15f875acea.gif",
        "https://i.pinimg.com/originals/7d/5d/52/7d5d52ae80b91a0640958342863f5275.gif",
        "https://i.pinimg.com/originals/2d/b4/64/2db464ad52e6c6236dece9136211f2b1.gif",
        "https://i.pinimg.com/originals/56/c7/3f/56c73f380d3ad747ff0600eb7ea1bbc7.gif",
        "https://i.pinimg.com/originals/1a/67/2c/1a672cef3d0d9d11f53650c43d3429ba.gif"
    ]

    gif_url = random.choice(gifs_abraço)

    embed = discord.Embed(
        description=random.choice(respostas),
        color=discord.Color.purple()
    )
    embed.set_image(url=gif_url)

    view = AbraçoView(ctx.author, membro, gif_url)
    mensagem = await ctx.send(embed=embed, view=view)
    view.message = mensagem  # Armazena a mensagem para edição futura

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
        "https://i.pinimg.com/originals/a6/e6/5a/a6e65ab98fc036a0f4bb677338abd6a9.gif",
        "https://i.pinimg.com/originals/7c/e6/c4/7ce6c444c0d69791db863a448132c9ed.gif",
        "https://i.pinimg.com/originals/95/19/2b/95192bdb70eb7e581db3e9af2032eac6.gif"
    ]
    await ctx.send(random.choice(gifs_choro))

@bot.command()
async def frase(ctx):
    frases = [
        "Ser verdadeiro incomoda quem vive de ilusões.",
        "As palavras machucam mais do que o silêncio de quem foi ferido.",
        "Nem toda distância é física, às vezes, é apenas falta de empatia.",
        "Antes de apontar, tente enxergar além das aparências.",
        "O julgamento alheio diz mais sobre quem julga do que sobre quem é julgado.",
        "Entre o que você mostra e o que realmente sente, há um abismo que poucos percebem.",
        "A verdade é um reflexo distorcido para quem só vê o que quer enxergar.",
        "Nem toda solidão é ausência, às vezes, é escolha.",
        "Ser mal compreendido é o preço de ser diferente.",
        "O que os outros pensam de você não define quem você realmente é.",
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

# Classe de seleção de ajuda
class AjudaSelect(Select):
    def __init__(self, author_id: int):
        self.author_id = author_id
        
        options = [
            discord.SelectOption(label="Diversão", description="Comandos para diversão 🎉", emoji="🎭"),
            discord.SelectOption(label="Utilidade", description="Comandos úteis para o dia a dia 🛠️", emoji="🔧"),
            discord.SelectOption(label="Economia", description="Comandos relacionados à economia 💰", emoji="💰"),
            discord.SelectOption(label="Voltar ao Início", description="Voltar ao menu principal 🔙", emoji="↩️"),
        ]
        
        super().__init__(placeholder="Selecione uma categoria:", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Desculpe, você não tem permissão para interagir com este menu. Só quem iniciou o comando pode utilizá-lo.",
                ephemeral=True
            )
            return

        categoria = self.values[0]
        embed = discord.Embed(color=discord.Color.blurple())

        if categoria == "Diversão":
            embed.title = "🎭 Comandos de Diversão"
            embed.description = (
                "`!rolar` - Rola um dado\n"
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
                "`!ping` - Mostra a latência\n"
                "`!avatar` - Exibe o avatar de um usuário\n"
                "`!convite` - Link do bot"
            )

        elif categoria == "Economia":
            embed.title = "💰 Comandos de Economia"
            embed.description = (
                "`!luzes` - Veja quantas luzes você tem\n"
                "`!rank` - Veja o ranking de luzes"
            )

        elif categoria == "Voltar ao Início":
            embed = discord.Embed(
                title="Ajuda da Luminarls",
                description=(
                    "💡 **A Luminarls é um bot de economia, diversão e utilidades!**\n\n"
                    "Selecione uma categoria abaixo para ver os comandos disponíveis."
                ),
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=AjudaView(self.author_id))
            return

        await interaction.response.edit_message(embed=embed)


# Classe da view que inclui o select
class AjudaView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id  # Guarda o ID de quem executou o comando
        self.add_item(AjudaSelect(author_id))

# Comando luzguia com prefixo "!"
@bot.command(name="luzguia", description="Mostra a central de comandos do bot.")
async def luzguia(ctx):
    embed = discord.Embed(
        title="Ajuda da Luminarls",
        description=(
            "💡 **A Luminarls é um bot de economia, diversão e utilidades!**\n\n"
            "Selecione uma categoria abaixo para ver os comandos disponíveis."
        ),
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    await ctx.send(embed=embed, view=AjudaView(ctx.author.id))

# Dicionário de tempo para mute
tempo_mute = {
    "s": 1,       # segundos
    "m": 60,      # minutos
    "h": 3600,    # horas
    "d": 86400,   # dias
    "w": 604800   # semanas
}

# Aplicar mute
async def aplicar_mute(ctx, membro, duracao):
    try:
        # Desabilitar envio de mensagens, criação de tópicos e conexão (em todos os canais)
        for canal in ctx.guild.text_channels + ctx.guild.voice_channels:
            await canal.set_permissions(membro, send_messages=False, connect=False, manage_channels=False, manage_threads=False, reason="Aplicação de mute")

        # Esperar pelo tempo de duração do mute
        await asyncio.sleep(duracao)

        # Reverter as permissões após o término do mute
        for canal in ctx.guild.text_channels + ctx.guild.voice_channels:
            await canal.set_permissions(membro, overwrite=None, reason="Expiração do mute")
    
    except discord.Forbidden:
        await ctx.send("❌ **Erro:** O bot não tem permissão para modificar permissões nos canais.")
    except Exception as e:
        await ctx.send(f"❌ **Erro inesperado:** {e}")

# Comando para mutar um usuário
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, membro: discord.Member, tempo: str):
    try:
        # Verificar se o tempo fornecido tem a última letra sendo a unidade (s, m, h, d, w)
        unidade = tempo[-1]  # Última letra (s, m, h, d, w)
        valor = tempo[:-1]   # Número antes da unidade
        
        # Verificar se a unidade é válida e o valor é um número
        if unidade in tempo_mute and valor.isdigit():
            duracao = int(valor) * tempo_mute[unidade]  # Calcular a duração
            await aplicar_mute(ctx, membro, duracao)
        else:
            await ctx.send("❌ **Formato inválido!** Use `60s`, `5m`, `1h`, `1d`, `1w`.")  # Mensagem de erro

    except Exception as e:
        await ctx.send(f"❌ **Erro inesperado:** {e}")

# Comando para desmutar um usuário
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, membro: discord.Member):
    try:
        # Restaurar permissões para todos os canais
        for canal in ctx.guild.text_channels + ctx.guild.voice_channels:
            await canal.set_permissions(membro, overwrite=None, reason="Desmute manual")
    
    except discord.Forbidden:
        await ctx.send("❌ **Erro:** O bot não tem permissão para modificar permissões nos canais.")
    except Exception as e:
        await ctx.send(f"❌ **Erro inesperado:** {e}")

AVISOS_FILE = "avisos.json"

# Carregar avisos do arquivo JSON
def carregar_avisos():
    if os.path.exists(AVISOS_FILE):
        with open(AVISOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Salvar avisos no arquivo JSON
def salvar_avisos():
    with open(AVISOS_FILE, "w", encoding="utf-8") as f:
        json.dump(warnings, f, indent=4)

warnings = carregar_avisos()  # Inicializa os avisos carregados do arquivo

@bot.command(name="warn")
async def warn(ctx, member: discord.Member, *, motivo="Sem motivo especificado"):
    """Avisa um usuário e aplica punições automáticas até o limite de 3 avisos."""
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if guild_id not in warnings:
        warnings[guild_id] = {}
    if user_id not in warnings[guild_id]:
        warnings[guild_id][user_id] = 0

    if warnings[guild_id][user_id] >= 3:
        await ctx.send(f"❌ {member.mention} já atingiu o limite de 3 avisos e foi expulso.")
        return

    warnings[guild_id][user_id] += 1
    salvar_avisos()  # Salva os avisos no arquivo JSON
    total_warnings = warnings[guild_id][user_id]

    # Aviso na DM
    try:
        await member.send(
            f"⚠️ Você recebeu um aviso no servidor **{ctx.guild.name}**!\n"
            f"**Motivo:** {motivo}\n"
            f"🔹 Total de Avisos: {total_warnings}\n"
            f"🕒 {hora_atual}\n"
            "Por favor, siga as regras para evitar punições."
        )
    except discord.Forbidden:
        await ctx.send(f"⚠️ {member.mention} não pôde receber a DM do aviso.")

    # Mensagem simples no chat
    await ctx.send(f"⚠️ {member.mention} recebeu um aviso! **({total_warnings}/3)** | 🕒 {hora_atual}")

    # Punições automáticas
    if total_warnings == 2:
        timeout_duration = timedelta(minutes=10)
        try:
            # Silenciar o usuário por 10 minutos
            await member.timeout(timeout_duration, reason="2 avisos acumulados")
            await ctx.send(f"🔇 {member.mention} foi silenciado por **10 minutos** após 2 avisos! | 🕒 {hora_atual}")
        except discord.Forbidden:
            await ctx.send(f"❌ Não tenho permissão para silenciar {member.mention}.")

    elif total_warnings == 3:
        try:
            # Expulsão do membro
            await member.kick(reason="Acúmulo de 3 avisos")
            await ctx.send(f"🚨 {member.mention} foi **expulso** por atingir 3 avisos! | 🕒 {hora_atual}")
            del warnings[guild_id][user_id]  # Resetar avisos após expulsão
            salvar_avisos()
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para expulsar este usuário.")

@bot.command(name="warns")
async def warns(ctx, member: discord.Member = None):
    """Mostra o número de avisos de um usuário. Se ninguém for mencionado, mostra os avisos do autor."""
    guild_id = str(ctx.guild.id)
    hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if member is None:
        member = ctx.author

    user_id = str(member.id)
    total_warnings = warnings.get(guild_id, {}).get(user_id, 0)

    if total_warnings == 0:
        await ctx.send(f"✅ {ctx.author.mention}, {member.mention} não tem avisos. | 🕒 {hora_atual}")
    else:
        await ctx.send(f"⚠️ {ctx.author.mention}, {member.mention} tem **{total_warnings}** aviso(s). | 🕒 {hora_atual}")

@bot.command(name="unwarn")
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx, member: discord.Member):
    """Remove todos os avisos de um usuário."""
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if guild_id in warnings and user_id in warnings[guild_id]:
        del warnings[guild_id][user_id]
        salvar_avisos()  # Atualiza o arquivo JSON
        await ctx.send(f"✅ Todos os avisos de {member.mention} foram removidos. | 🕒 {hora_atual}")
    else:
        await ctx.send(f"⚠️ {member.mention} não tem avisos para remover. | 🕒 {hora_atual}")
        
# ID do dono do bot (substitua pelo seu ID)
OWNER_ID = 1304135629990269033  

# Link do servidor
SERVER_LINK = "https://discord.gg/XnuTBECY99"

# Regras do servidor
REGRAS = {
    "1️⃣ Respeito": "Seja educado e evite ofensas.",
    "2️⃣ Sem Spam": "Não flood ou envie mensagens repetidas.",
    "3️⃣ Conteúdo": "Nada de NSFW ou ilegal.",
    "4️⃣ Links": "Evite links suspeitos ou maliciosos.",
    "5️⃣ Staff": "Siga as instruções dos moderadores.",
}

# Classe do botão
class RegrasView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="🌙 Entre no Lumi", url=SERVER_LINK, style=discord.ButtonStyle.link))

# Comando de regras (apenas para o dono do bot)
@bot.command()
async def regras(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Apenas o dono do bot pode usar este comando.", delete_after=5)

    await ctx.message.delete()
    
    embed = discord.Embed(
        title="📜 Regras",
        description="Leia e siga as regras para um bom convívio.",
        color=discord.Color.blue()
    )

    for titulo, descricao in REGRAS.items():
        embed.add_field(name=titulo, value=descricao, inline=False)

    embed.set_footer(text="Dúvidas? Entre no Lumi!")

    await ctx.send(embed=embed, view=RegrasView())

@bot.command(name="serverstats")
async def serverstats(ctx):
    """Exibe estatísticas do servidor."""
    guild = ctx.guild
    total_members = guild.member_count
    total_text_channels = len(guild.text_channels)
    total_voice_channels = len(guild.voice_channels)
    total_categories = len(guild.categories)
    total_roles = len(guild.roles)
    
    embed = discord.Embed(
        title=f"Estatísticas do Servidor: {guild.name}",
        description="Aqui estão as estatísticas do servidor!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Membros", value=f"{total_members} membros", inline=False)
    embed.add_field(name="Canais de Texto", value=f"{total_text_channels} canais", inline=False)
    embed.add_field(name="Canais de Voz", value=f"{total_voice_channels} canais", inline=False)
    embed.add_field(name="Categorias", value=f"{total_categories} categorias", inline=False)
    embed.add_field(name="Cargos", value=f"{total_roles} cargos", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def totalcmd(ctx):
    comandos_por_categoria = {
        "📌 Utilidade": ["ping - Mostra a latência", "avatar - Exibe o avatar de um usuário", "convite - Link do bot"],
        "💡 Sistema de Luzes": ["luzes - Veja quantas luzes você tem", "rank - Veja o ranking de luzes"],
        "🎉 Diversão": [
            "coinflip - Cara ou coroa",
            "abraço - Envie um abraço para alguém 🤗",
            "beijo - Dê um beijo em alguém 💋",
            "tapinha - Dê um tapinha em alguém ✋",
            "chorar - Demonstre sua tristeza 😢",
            "frase - Receba uma frase aleatória 📜"
        ],
        "🎮 Jogos": ["rolar - Rola um dado"]
    }

    categorias = list(comandos_por_categoria.keys())  # Lista das categorias
    categoria_atual = 0  # Começa na primeira categoria

    def criar_embed():
        nome_categoria = categorias[categoria_atual]
        comandos = comandos_por_categoria[nome_categoria]
        embed = discord.Embed(
            title=f"{nome_categoria} - Comandos",
            description=f"📜 **Total de comandos na categoria:** {len(comandos)}",
            color=discord.Color.blue()
        )
        comandos_formatados = "\n".join(f"`!{cmd}`" for cmd in comandos)
        embed.add_field(name="Comandos disponíveis:", value=comandos_formatados, inline=False)
        embed.set_footer(text=f"Categoria {categoria_atual + 1} de {len(categorias)}")
        return embed

    mensagem = await ctx.send(embed=criar_embed())

    if len(categorias) > 1:
        await mensagem.add_reaction("◀️")  # Voltar
        await mensagem.add_reaction("▶️")  # Avançar

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == mensagem.id and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "▶️" and categoria_atual < len(categorias) - 1:
                    categoria_atual += 1
                elif str(reaction.emoji) == "◀️" and categoria_atual > 0:
                    categoria_atual -= 1

                await mensagem.edit(embed=criar_embed())
                await mensagem.remove_reaction(reaction.emoji, user)

            except asyncio.TimeoutError:
                break  # Para a interação se o usuário não reagir após 60 segundos

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

@bot.tree.command(name="convite", description="Obtenha o link para adicionar o bot ao seu servidor")
async def convite(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌙 **Adicione Luminarls ao seu servidor!**",
        description="Melhore seu servidor com meus recursos avançados. Clique nos botões abaixo! 🚀",
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url=interaction.client.user.avatar.url)
    embed.set_footer(text="Estou pronta para ajudar no seu servidor!", icon_url=interaction.client.user.avatar.url)

    view = InviteButton()  # Instancia a view com os botões

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)  # Envia a embed com botões
    
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
            discord.SelectOption(label="Diversão", description="Comandos para diversão 🎉", emoji="🎭"),
            discord.SelectOption(label="Utilidade", description="Comandos úteis para o dia a dia 🛠️", emoji="🔧"),
            discord.SelectOption(label="Economia", description="Comandos relacionados à economia 💰", emoji="💰"),
            discord.SelectOption(label="Voltar ao Início", description="Voltar ao menu principal 🔙", emoji="↩️"),
        ]
        
        super().__init__(placeholder="Selecione uma categoria:", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Desculpe, você não tem permissão para interagir com este menu. Só quem iniciou o comando pode utilizá-lo.",
                ephemeral=True
            )
            return

        categoria = self.values[0]
        embed = discord.Embed(color=discord.Color.blurple())

        if categoria == "Diversão":
            embed.title = "🎭 Comandos de Diversão"
            embed.description = (
                "`!rolar` - Rola um dado\n"
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
                "`!ping` - Mostra a latência\n"
                "`!avatar` - Exibe o avatar de um usuário\n"
                "`!convite` - Link do bot"
            )

        elif categoria == "Economia":
            embed.title = "💰 Comandos de Economia"
            embed.description = (
                "`!luzes` - Veja quantas luzes você tem\n"
                "`!rank` - Veja o ranking de luzes"
            )

        elif categoria == "Voltar ao Início":
            embed = discord.Embed(
                title="Ajuda da Luminarls",
                description=(
                    "💡 **A Luminarls é um bot de economia, diversão e utilidades!**\n\n"
                    "Selecione uma categoria abaixo para ver os comandos disponíveis."
                ),
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=AjudaView(self.author_id))
            return

        await interaction.response.edit_message(embed=embed)

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
    embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
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
        title="🌙 Sobre a Luminarls",
        description=(
            f"Eu estou atualmente em **{total_servidores} servidores** e tenho **{total_comandos} comandos**.\n\n"
            "Fui criada em **18 de março** para tornar os servidores mais **divertidos e inteligentes**!\n\n"
            "Eu fui programada em **Python** usando **discord.py** e me mantenho online usando a **hospedagem do Visual Studio**.\n\n"
            "💜 Desenvolvida por `crazy`"
        ),
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1351585153209597992/a0c671f9c2819ef8511c843e1ee9b947.png?size=1024")
    embed.add_field(name="🔗 Me adicione", value="[Clique aqui](https://discord.com/oauth2/authorize?client_id=1351585153209597992&permissions=1153400515923127&integration_type=0&scope=bot)", inline=True)
    embed.add_field(name="🛠 Servidor de Suporte", value="[Entre aqui](https://discord.gg/XnuTBECY99)", inline=True)

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
async def on_message(message):
    # Evita que o bot responda a si mesmo
    if message.author.bot:
        return

    # Verifica se o bot foi mencionado diretamente na mensagem
    if message.content.startswith(f"<@{bot.user.id}>") or message.content.startswith(f"<@!{bot.user.id}>"):
        await message.channel.send(
            f"Olá {message.author.mention}! Meu prefixo neste servidor é `!`. Para ver meus comandos, use `!cmd` em slash `/luzguia`."
        )

    # Processa outros comandos do bot
    # Apenas processa comandos se a mensagem não for uma menção ao bot
    if not message.content.startswith(f"<@{bot.user.id}>") and not message.content.startswith(f"<@!{bot.user.id}>"):
        await bot.process_commands(message)

status_list = [
    ("Jogando", "Explorando 🌍"),
    ("Jogando", "Xadrez cósmico ♟️"),
    ("Jogando", "Criando mundos 🏗️"),
    ("Jogando", "sky filhos da luz ⏳"),
    ("Ouvindo", "ecos do espaço 🔊"),
    ("Ouvindo", "sussurros do vento 🍃"),
    ("Assistindo", "as estrelas ✨"),
    ("Assistindo", "o tempo voar ⏲️"),
    ("Jogando", "use !luzguia ⭐"),  # Mantém o /luzguia visível
    ("Jogando", "iluminando servidores 💡"),  # Frase do bot
]

async def change_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        activity_type, text = random.choice(status_list)

        if activity_type == "Jogando":
            activity = discord.Game(name=text)
        elif activity_type == "Ouvindo":
            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif activity_type == "Assistindo":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)

        await bot.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(60)  # Troca o status a cada 60 segundos

@bot.event
async def on_ready():
    print(f'✅ {bot.user} está online!')
    try:
        synced = await bot.tree.sync()
        print(f'📌 {len(synced)} comandos de barra sincronizados!')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

    # Inicia a troca de status
    bot.loop.create_task(change_status())

# Inicia o bot com o token
bot.run(TOKEN)
