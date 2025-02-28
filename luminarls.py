
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
from discord.utils import get
import asyncio
import time
import db

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
    start_time = time.perf_counter()  # Início do tempo real
    message = await ctx.send("🏓 Calculando latência...")  # Mensagem temporária
    end_time = time.perf_counter()  # Fim do tempo real

    latency = round(bot.latency * 1000, 2)  # Latência API em ms (com duas casas decimais)
    response_time = round((end_time - start_time) * 1000, 2)  # Tempo real de resposta em ms

    embed = discord.Embed(
        title="🏓 Pong!",
        description="📡 **Latência em tempo real:**",
        color=discord.Color.blue()
    )
    embed.add_field(name="🌍 API do Discord", value=f"**{latency}ms**", inline=True)
    embed.add_field(name="⚡ Resposta do Bot", value=f"**{response_time}ms**", inline=True)
    embed.set_footer(text="Luminarls • Sempre pronta para ajudar!", icon_url=bot.user.avatar.url)

    await message.edit(content=None, embed=embed)  # Edita a mensagem com o embed atualizado

@bot.command(name="cmd")  # Define o comando como "!cmd"
async def cmd(ctx):  
    embed = discord.Embed(
        title="📌 Central de Comandos",
        description="Explore os comandos disponíveis do Luminarls:",
        color=discord.Color.dark_gray()
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1331060223833673819/827885bea276a81d4a5e63fbe8cc74c2.png?size=1024")

    embed.add_field(
        name="💡 Economia", 
        value="`!luzes` ou `!Luzes` - Resgate diário\n`!luz` - Ver saldo atual\n`+pay @usuário quantidade` - Transferir luzes", 
        inline=False
    )

    embed.add_field(
        name="🖼 Avatar", 
        value="`!avatar` - Veja o avatar de um usuário", 
        inline=False
    )

    embed.add_field(
        name="🏆 Ranking",
        value="`!rank luzes local ` - Ranking do servidor\n`!rank luzes ` - Ranking global\nPadrão: 10 usuários por página, use botões para navegar",
        inline=False
    )

    embed.add_field(
        name="🌟 Convite",
        value="`!convite` - Adicione-me ao seu servidor!",
        inline=False
    )

    embed.set_footer(text="Use o prefixo `!` para executar os comandos.")

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
    if user_id not in db.db:
        db.db[user_id] = {"luzes": 0, "last_claimed": "2000-01-01 00:00:00"}
        db.save()

def obter_ranking():
    """Ordena os usuários pelo total de luzes."""
    return sorted(db.db.items(), key=lambda x: x[1]["luzes"], reverse=True)

@bot.command(name="luzes", aliases=["Luzes"])
async def luzes(ctx):
    """Comando para coletar luzes a cada 5 minutos e exibir contagem regressiva."""
    user_id = str(ctx.author.id)
    agora = datetime.utcnow()
    criar_usuario(user_id)

    ultimo_resgate = datetime.strptime(db.db[user_id]["last_claimed"], "%Y-%m-%d %H:%M:%S")
    tempo_passado = agora - ultimo_resgate

    if tempo_passado >= TEMPO_ESPERA:
        luzes_coletadas = calcular_luzes(BASE_LUZES)
        db.db[user_id]["luzes"] += luzes_coletadas
        db.db[user_id]["last_claimed"] = agora.strftime("%Y-%m-%d %H:%M:%S")
        db.save()

        ranking = obter_ranking()
        user_rank = next((i + 1 for i, (uid, _) in enumerate(ranking) if uid == user_id), "N/A")

        # Lista de frases aleatórias para exibir quando coletar luzes
        frases_coleta = [
            f"🎉 | {ctx.author.mention}, você coletou **{luzes_coletadas}** luzes!",
            f"✨ | Uau, {ctx.author.mention}! **{luzes_coletadas}** luzes foram adicionadas ao seu inventário!",
            f"💡 | {ctx.author.mention}, você acaba de resgatar **{luzes_coletadas}** luzes brilhantes!",
            f"🌟 | Incrível, {ctx.author.mention}! Você encontrou **{luzes_coletadas}** luzes reluzentes!",
            f"⚡ | {ctx.author.mention}, você coletou **{luzes_coletadas}** luzes energizantes!"
        ]

        # Escolhe uma frase aleatória
        frase_escolhida = random.choice(frases_coleta)

        embed = discord.Embed(
            title="✨ Luzes Coletadas! ✨",
            description=(
                f"{frase_escolhida}\n"
                f"🌟 | Total: **{db.db[user_id]['luzes']:,}** luzes acumuladas.\n"
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

        while segundos_restantes > 0:
            await asyncio.sleep(1)
            segundos_restantes -= 1
            embed.description = (
                f"⚠️ | {ctx.author.mention}, você já coletou luzes recentemente.\n"
                f"🕒 | Próximo resgate disponível em {format_time(segundos_restantes)}."
            )
            await message.edit(embed=embed)

        embed.title = "✅ Pronto para coletar!"
        embed.description = f"🎉 | {ctx.author.mention}, você já pode coletar suas luzes novamente!"
        embed.color = discord.Color.green()
        await message.edit(embed=embed)
        await ctx.send(f"{ctx.author.mention} agora pode resgatar suas luzes! 🚀")

@bot.command()
async def luz(ctx):
    """Comando para verificar quantas luzes o usuário tem."""
    user_id = str(ctx.author.id)

    # Garante que o usuário existe no banco de dados
    criar_usuario(user_id)

    luzes = db.db[user_id]["luzes"]

    embed = discord.Embed(
        title="💡 Suas Luzes",
        description=f"{ctx.author.mention}, você tem **{luzes:,}** luzes! ✨",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

class RankingView(discord.ui.View):
    def __init__(self, ranking, is_local, page_size=10, timeout=60):
        super().__init__(timeout=timeout)
        self.ranking = ranking
        self.current_page = 0
        self.page_size = page_size
        self.total_pages = (len(ranking) - 1) // page_size + 1
        self.is_local = is_local

        # Desativa botões se só houver uma página
        if self.total_pages <= 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=await self.get_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Próxima ➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=await self.get_embed(), view=self)
        else:
            await interaction.response.defer()

    async def get_embed(self):
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.ranking))
        current_page_items = self.ranking[start_idx:end_idx]

        if self.is_local:
            total_luzes = sum(luzes for _, luzes in self.ranking)
            embed = discord.Embed(
                title=f"🏆 **Ranking Local - Página {self.current_page + 1}/{self.total_pages}**",
                description=f"**Total de luzes no servidor**: {total_luzes} luzes 🌟",
                color=discord.Color.green()
            )

            for i, (user_id, luzes) in enumerate(current_page_items, start=start_idx + 1):
                try:
                    user = await bot.fetch_user(user_id)
                    # Adicionando medalhas para os três primeiros
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

                    # Formata a entrada com avatar do usuário
                    embed.add_field(
                        name=f"{medal} {user.name}",
                        value=f"{luzes} luzes ✨",
                        inline=False
                    )
                    # Adiciona o avatar do usuário como thumbnail para o primeiro colocado
                    if i == 1 and self.current_page == 0:
                        embed.set_thumbnail(url=user.display_avatar.url)
                except discord.NotFound:
                    continue
        else:
            total_luzes_global = sum(data.get("luzes", 0) for _, data in self.ranking)
            total_usuarios = len(self.ranking)

            embed = discord.Embed(
                title=f"🌟 **Ranking Global - Página {self.current_page + 1}/{self.total_pages}**",
                description=f"**Total de luzes acumuladas globalmente**: {total_luzes_global} luzes 🌍\n**Total de usuários**: {total_usuarios}",
                color=discord.Color.purple()
            )

            for i, (user_id, data) in enumerate(current_page_items, start=start_idx + 1):
                try:
                    user = await bot.fetch_user(int(user_id))
                    # Formatação para posição no ranking
                    position = f"#{i}"

                    # Formata a entrada com avatar do usuário
                    embed.add_field(
                        name=f"{position} {user.name}",
                        value=f"{data.get('luzes', 0)} luzes",
                        inline=False
                    )
                    # Adiciona o avatar do usuário como thumbnail para o primeiro colocado
                    if i == 1 and self.current_page == 0:
                        embed.set_thumbnail(url=user.display_avatar.url)
                except discord.NotFound:
                    continue

        embed.set_footer(text=f"Mostrando {start_idx + 1}-{end_idx} de {len(self.ranking)} usuários com luzes")
        return embed

@bot.command()
async def rank(ctx, tipo: str = "luzes", page_size: int = 10):
    """
    Exibe os rankings locais ou globais com base nas luzes dos usuários.
    Uso: !rank luzes [tamanho_pagina] ou !rank luzes local [tamanho_pagina]
    """
    # Verifica se o tamanho da página está entre 1 e 25
    if page_size < 1:
        page_size = 1
    elif page_size > 25:
        page_size = 25  # Define um máximo de 25 usuários por página

    tipo_parts = tipo.lower().split()
    tipo_principal = tipo_parts[0]

    # Verifica se é um ranking local
    if len(tipo_parts) > 1 and tipo_parts[1] == "local":
        if ctx.guild:
            ranking = sorted(
                [(member.id, db.db.get(str(member.id), {}).get("luzes", 0))
                 for member in ctx.guild.members if str(member.id) in db.db and db.db.get(str(member.id), {}).get("luzes", 0) > 0],
                key=lambda x: x[1], reverse=True)

            if not ranking:
                await ctx.send("Ainda não há dados suficientes para exibir o ranking local.")
                return

            view = RankingView(ranking, is_local=True, page_size=page_size)
            await ctx.send(embed=await view.get_embed(), view=view)
        else:
            await ctx.send("Este comando está disponível apenas em servidores.")

    elif tipo_principal == "luzes":
        # Filtra apenas usuários com luzes > 0
        ranking = [(user_id, data) for user_id, data in db.db.items() 
                  if data.get("luzes", 0) > 0]

        # Ordena pelo total de luzes
        ranking = sorted(ranking, key=lambda x: x[1].get("luzes", 0), reverse=True)

        if not ranking:
            await ctx.send("Ainda não há dados suficientes para exibir o ranking global.")
            return

        view = RankingView(ranking, is_local=False, page_size=page_size)
        await ctx.send(embed=await view.get_embed(), view=view)

    else:
        await ctx.send("Por favor, informe um tipo de ranking válido: `!rank luzes [tamanho_pagina]` ou `!rank luzes local [tamanho_pagina]`.")

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

@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    """Exibe informações detalhadas sobre um usuário com um embed mais animado."""
    if member is None:
        member = ctx.author  # Se ninguém for mencionado, pega o autor do comando

    # Cor baseada no papel mais alto do usuário (se disponível)
    color = member.color if member.color != discord.Color.default() else discord.Color.blue()

    embed = discord.Embed(
        title=f"🌟 Informações de {member.name}",
        description=f"🔹 Aqui estão os detalhes sobre {member.mention}:",
        color=color
    )

    embed.set_thumbnail(url=member.display_avatar.url)

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

    # Envia a embed com as informações
    await ctx.send(embed=embed)

class InviteButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="🔗 Adicionar Luminarls",
            url="https://discord.com/oauth2/authorize?client_id=1331060223833673819&permissions=8&integration_type=0&scope=bot+applications.commands",
            style=discord.ButtonStyle.link
        ))
        self.add_item(discord.ui.Button(
            label="adicione na sua conta",
            url="https://discord.com/oauth2/authorize?client_id=1331060223833673819",  # Substitua pelo link real do seu servidor de suporte
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

    luzes_antes = db.db[user_id].get("luzes", 0)
    db.db[user_id]["luzes"] += quantidade
    db.save()

    embed = discord.Embed(
        title="💡 Luzes Adicionadas",
        description=f"✅ | {quantidade} luzes foram adicionadas para {user.mention}.\n💡 | **{luzes_antes}** → **{db.db[user_id]['luzes']}** luzes",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Ação executada por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="pay")
async def pay(ctx, user: discord.Member = None, quantidade: int = None):
    """
    Comando para transferir luzes para outro usuário com botão de confirmação.
    Uso: !pay @usuário quantidade
    """
    if not user or quantidade is None:
        embed = discord.Embed(
            title="❌ Erro no Comando",
            description="Formato incorreto! Use `!pay @usuário quantidade`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if user.id == ctx.author.id:
        embed = discord.Embed(
            title="❌ Transferência Inválida",
            description="Você não pode transferir luzes para si mesmo.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if user.bot:
        embed = discord.Embed(
            title="❌ Transferência Inválida",
            description="Você não pode transferir luzes para bots.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if quantidade <= 0:
        embed = discord.Embed(
            title="❌ Quantidade Inválida",
            description="A quantidade de luzes deve ser um número positivo.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # IDs dos usuários
    autor_id = str(ctx.author.id)
    destinatario_id = str(user.id)

    # Garante que ambos usuários existem no banco de dados
    criar_usuario(autor_id)
    criar_usuario(destinatario_id)

    # Verifica se o autor tem luzes suficientes
    luzes_autor = db.db[autor_id].get("luzes", 0)

    if luzes_autor < quantidade:
        await ctx.send(f"❌ | Você não tem luzes suficientes. Seu saldo atual é de **{luzes_autor}** luzes.")
        return

    class PaymentButtons(discord.ui.View):
        def __init__(self, timeout=60):
            super().__init__(timeout=timeout)
            self.value = None

        @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.green, emoji="✅")
        async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user.id:
                await interaction.response.send_message("❌ | Apenas o destinatário pode aceitar esta transferência!", ephemeral=True)
                return

            self.value = True
            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(view=self)
            self.stop()

        @discord.ui.button(label="Recusar", style=discord.ButtonStyle.red, emoji="❌")
        async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user.id:
                await interaction.response.send_message("❌ | Apenas o destinatário pode recusar esta transferência!", ephemeral=True)
                return

            self.value = False
            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(view=self)
            self.stop()

    # Cria a mensagem de solicitação de transferência
    embed = discord.Embed(
        title="💰 Solicitação de Transferência",
        description=f"{ctx.author.mention} deseja transferir **{quantidade}** luzes para {user.mention}.",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="📝 Detalhes",
        value=f"• **Remetente:** {ctx.author.name}\n• **Destinatário:** {user.name}\n• **Quantidade:** {quantidade} luzes",
        inline=False
    )

    embed.set_footer(text="Esta solicitação expira em 60 segundos.")

    # Cria os botões e envia a mensagem
    view = PaymentButtons()
    message = await ctx.send(f"{user.mention}, você recebeu uma solicitação de transferência!", embed=embed, view=view)

    # Aguarda a resposta ou timeout
    await view.wait()

    if view.value is None:
        # Timeout - nenhuma resposta recebida
        for item in view.children:
            item.disabled = True

        embed.description = f"⏱️ | A solicitação de transferência de {ctx.author.mention} para {user.mention} expirou."
        embed.color = discord.Color.dark_gray()
        await message.edit(embed=embed, view=view)

    elif view.value:
        # Transferência aceita - processa a transferência
        db.db[autor_id]["luzes"] -= quantidade
        db.db[destinatario_id]["luzes"] += quantidade
        db.save()

        success_embed = discord.Embed(
            title="✅ Transferência Realizada!",
            description=f"{ctx.author.mention} transferiu **{quantidade}** luzes para {user.mention}!",
            color=discord.Color.green()
        )

        # Informações de saldo para ambos
        success_embed.add_field(
            name=f"💰 Saldo de {ctx.author.name}",
            value=f"**{luzes_autor}** → **{db.db[autor_id]['luzes']}** luzes",
            inline=True
        )

        success_embed.add_field(
            name=f"💰 Saldo de {user.name}",
            value=f"**{db.db[destinatario_id].get('luzes', 0) - quantidade}** → **{db.db[destinatario_id]['luzes']}** luzes",
            inline=True
        )

        success_embed.set_footer(text="Transferência concluída com sucesso! ✨")
        await message.edit(embed=success_embed)

    else:
        # Transferência recusada
        decline_embed = discord.Embed(
            title="❌ Transferência Recusada",
            description=f"{user.mention} recusou a transferência de **{quantidade}** luzes de {ctx.author.mention}.",
            color=discord.Color.red()
        )

        decline_embed.set_footer(text="Nenhuma luzes foi transferida.")
        await message.edit(embed=decline_embed)

def save_db():
    db.save()

@bot.command(name="reset")
@commands.has_permissions(administrator=True)  # Restrito a administradores
async def reset(ctx, tipo: str = None, user: discord.Member = None):
    """
    Comando para resetar luzes de um usuário específico ou de todos os usuários.
    Uso: !reset luzes @usuário ou !reset luzes
    """
    if not tipo or tipo.lower() != "luzes":
        await ctx.send("❌ | Comando incorreto. Use `!reset luzes @usuário` ou `!reset luzes` para resetar todos.")
        return

    if user:  # Resetar luzes de um usuário específico
        user_id = str(user.id)
        if user_id in db.db:
            old_luzes = db.db[user_id].get("luzes", 0)
            db.db[user_id]["luzes"] = 0
            save_db()  # Salva os dados após reset

            embed = discord.Embed(
                title="🔄 Reset de Luzes",
                description=f"✅ | As luzes de {user.mention} foram resetadas.\n💡 | **{old_luzes}** → **0** luzes",
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Ação executada por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ | {user.mention} não possui registro de luzes no sistema.")
    else:  # Resetar luzes de todos os usuários
        # Confirmação para evitar acidentes
        confirm_msg = await ctx.send("⚠️ | Você está prestes a resetar as luzes de **TODOS OS USUÁRIOS**. Esta ação não pode ser desfeita!\n\nReaja com ✅ para confirmar ou ❌ para cancelar.")
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "✅":
                # Conta total de luzes antes do reset
                total_antes = sum(data.get("luzes", 0) for _, data in db.db.items())
                user_count = 0

                # Reset para todos
                for user_id in db.db:
                    if "luzes" in db.db[user_id]:
                        db.db[user_id]["luzes"] = 0
                        user_count += 1
                
                save_db()  # Salva os dados após reset

                embed = discord.Embed(
                    title="🔄 Reset Global de Luzes",
                    description=f"✅ | Reset completo! As luzes de **{user_count}** usuários foram zeradas.\n💡 | Total resetado: **{total_antes}** luzes",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Ação executada por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("🛑 | Reset cancelado.")

        except asyncio.TimeoutError:
            await ctx.send("⏱️ | Tempo esgotado. Reset cancelado.")

@bot.tree.command(name="luzes", description="Coletar luzes a cada 5 minutos.")
async def slash_luzes(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    agora = datetime.utcnow()
    criar_usuario(user_id)
    ultimo_resgate = datetime.strptime(db.db[user_id]["last_claimed"], "%Y-%m-%d %H:%M:%S")
    tempo_passado = agora - ultimo_resgate

    if tempo_passado >= TEMPO_ESPERA:
        luzes_coletadas = calcular_luzes(BASE_LUZES)
        db.db[user_id]["luzes"] += luzes_coletadas
        db.db[user_id]["last_claimed"] = agora.strftime("%Y-%m-%d %H:%M:%S")
        db.save()
        
        ranking = obter_ranking()
        user_rank = next((i + 1 for i, (uid, _) in enumerate(ranking) if uid == user_id), "N/A")

        frases_coleta = [
            f"🎉 | {interaction.user.mention}, você coletou **{luzes_coletadas}** luzes!",
            f"✨ | Uau, {interaction.user.mention}! **{luzes_coletadas}** luzes foram adicionadas ao seu inventário!",
        ]
        frase_escolhida = random.choice(frases_coleta)
        embed = discord.Embed(
            title="✨ Luzes Coletadas! ✨",
            description=(
                f"{frase_escolhida}\n🌟 | Total: **{db.db[user_id]['luzes']:,}** luzes acumuladas.\n🏆 | Ranking: **#{user_rank}**"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        tempo_restante = TEMPO_ESPERA - tempo_passado
        segundos_restantes = int(tempo_restante.total_seconds())

        embed = discord.Embed(
            title="⏳ Tempo de Espera",
            description=(
                f"⚠️ | {interaction.user.mention}, você já coletou luzes recentemente.\n"
                f"🕒 | Próximo resgate disponível em **{segundos_restantes // 60}m {segundos_restantes % 60}s**."
            ),
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="luz", description="Ver quantas luzes você tem.")
async def slash_luz(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    criar_usuario(user_id)
    luzes = db.db[user_id]["luzes"]
    embed = discord.Embed(
        title="💡 Suas Luzes",
        description=f"{interaction.user.mention}, você tem **{luzes:,}** luzes! ✨",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rank", description="Exibe o ranking de luzes.")
async def slash_rank(interaction: discord.Interaction, tipo: str = "luzes"):
    ranking = obter_ranking()
    if not ranking:
        await interaction.response.send_message("Ainda não há dados suficientes para exibir o ranking.", ephemeral=True)
        return

    embed = discord.Embed(title="🏆 Ranking Global", color=discord.Color.purple())
    for i, (user_id, data) in enumerate(ranking[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            embed.add_field(name=f"#{i}", value=f"{user.mention} - {data.get('luzes', 0)} luzes ✨", inline=False)
        except:
            embed.add_field(name=f"#{i}", value=f"ID: {user_id} - {data.get('luzes', 0)} luzes ✨", inline=False)

    embed.set_footer(text=f"Mostrando os top 10 de {len(ranking)} usuários.")
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_guild_join(guild):
    log_channel = bot.get_channel(1345136764490223666)  # Substitua pelo ID de um canal onde deseja registrar

    # Verifica quem tem permissão de "Gerenciar Servidor" (possível responsável por adicionar)
    adms = [member for member in guild.members if member.guild_permissions.manage_guild]
    
    if adms:
        dono = adms[0]  # Pega o primeiro da lista (geralmente um dos responsáveis)
        msg = f"🔹 O bot foi adicionado ao servidor **{guild.name}**\n👑 Possível responsável: {dono.mention} ({dono.id})"
    else:
        msg = f"🔹 O bot foi adicionado ao servidor **{guild.name}**, mas não foi possível identificar quem adicionou."

    if log_channel:
        await log_channel.send(msg)

    print(msg)  # Também imprime no console

@bot.command()
@commands.is_owner()  # Apenas o dono do bot pode usar
async def servidores(ctx):
    guilds = sorted(bot.guilds, key=lambda g: g.name.lower())  # Ordena alfabeticamente
    servidores_lista = "\n".join([f"{i+1}. {guild.name} (ID: {guild.id})" for i, guild in enumerate(guilds)])
    
    if not servidores_lista:
        servidores_lista = "O bot não está em nenhum servidor."

    await ctx.send(f"🌍 O bot está nos seguintes servidores:\n```{servidores_lista}```")

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

@bot.command()
@commands.is_owner()  # Apenas o dono do bot pode usar
async def remover(ctx, *, servidor: str = None):
    if servidor is None:
        guild = ctx.guild  # Sai do servidor atual se nenhum nome/ID for informado
    else:
        # Tenta encontrar o servidor pelo ID
        guild = bot.get_guild(int(servidor)) if servidor.isdigit() else None
        
        # Se não encontrar pelo ID, busca pelo nome (case insensitive)
        if guild is None:
            guild = discord.utils.find(lambda g: g.name.lower() == servidor.lower(), bot.guilds)

    if guild:
        await ctx.send(f"👋 Saindo do servidor **{guild.name}**...")
        await guild.leave()
    else:
        await ctx.send("❌ O bot não está nesse servidor ou o nome/ID é inválido.")

# Configuração para VS Code
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("⚠️ Token não encontrado no arquivo .env. Verifique se o token está definido corretamente.")
        token = input("Digite o token do bot: ")
except ImportError:
    print("python-dotenv não está instalado. Execute: pip install python-dotenv")
    token = input("Digite o token do bot: ")

# Inicia o bot com o token
bot.run(token)