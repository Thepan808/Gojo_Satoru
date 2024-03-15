from datetime import datetime
from io import BytesIO
from traceback import format_exc

from pyrogram.errors import MessageTooLong, PeerIdInvalid, UserIsBlocked
from pyrogram.types import Message

from Powers import LOGGER, MESSAGE_DUMP, SUPPORT_GROUP, TIME_ZONE
from Powers.bot_class import Gojo
from Powers.database.antispam_db import GBan
from Powers.database.users_db import Users
from Powers.supports import get_support_staff
from Powers.utils.clean_file import remove_markdown_and_html
from Powers.utils.custom_filters import command
from Powers.utils.extract_user import extract_user
from Powers.utils.parser import mention_html
from Powers.vars import Config

# Initialize
db = GBan()
SUPPORT_STAFF = get_support_staff()

@Gojo.on_message(command(["gban", "globalban"], sudo_cmd=True))
async def gban(c: Gojo, m: Message):
    if len(m.text.split()) == 1:
        await m.reply_text(
            text="<b>Como gban?</b> \n <b>Responder:</b> <code>/gban user_id reason</code>"
        )
        return

    if len(m.text.split()) == 2 and not m.reply_to_message:
        await m.reply_text(text="Por favor, insira um motivo para o usuário gban!")
        return

    user_id, user_first_name, _ = await extract_user(c, m)

    if m.reply_to_message:
        gban_reason = m.text.split(None, 1)[1]
    else:
        gban_reason = m.text.split(None, 2)[2]

    if user_id in SUPPORT_STAFF:
        await m.reply_text(text="Este usuário faz parte do meu Suporte!, Não podemos banir os nossos!")
        return

    if user_id == Config.BOT_ID:
        await m.reply_text(
            text="Você não se atreve a usar esse comando em mim novamente nigga! \n Vá direto e foda-se......"
        )
        return

    if db.check_gban(user_id):
        db.update_gban_reason(user_id, gban_reason)
        await m.reply_text(text="Razão Gban atualizada para: <code>{gban_reason}</code>.")
        return

    db.add_gban(user_id, gban_reason, m.from_user.id)
    await m.reply_text(
        (
            f"Adicionado {user_first_name} para Lista GBan. \n Eles agora serão banidos em todos os grupos onde eu sou administrador!"
        )
    )
    LOGGER.info(f"{m.from_user.id} gbanido {user_id} De {m.chat.id}")
    date = datetime.utcnow().strftime("%H:%M - %d-%m-%Y")
    log_msg = f"#GBAN \n <b>Originado de:</b> {m.chat.id} \n <b>Admin:</b> {await mention_html(m.from_user.first_name, m.from_user.id)} \n <b>Gbanido User:</b> {await mention_html(user_first_name, user_id)} \n <b>Gbanned User ID:</b> {user_id} \\ n<b>Event Stamp:</b> {date}"
    await c.send_message(MESSAGE_DUMP, log_msg)
    try:
        # Send message to user telling that he's gbanned
        await c.send_message(
            user_id,
            f"Você foi adicionado à minha lista de banimento global! \n <b>Razão:</b> <code>{gban_reason}</code> \n <b>Chat de Apelação:</b> @{SUPPORT_GROUP}",
        )
    except UserIsBlocked:
        LOGGER.error("Não foi possível enviar mensagem PM, usuário bloqueado bot")
    except PeerIdInvalid:
        LOGGER.error(
            "Não vi este usuário em lugar nenhum, mente encaminhar uma de suas mensagens para mim?",
        )
    except Exception as ef:  # TO DO: Improve Error Detection
        LOGGER.error(ef)
        LOGGER.error(format_exc())
    return


@Gojo.on_message(
    command(["ungban", "unglobalban", "globalunban"], sudo_cmd=True),
)
async def ungban(c: Gojo, m: Message):
    if len(m.text.split()) == 1:
        await m.reply_text(text="Passar um ID de usuário ou nome de usuário como um argumento!")
        return

    user_id, user_first_name, _ = await extract_user(c, m)

    if user_id in SUPPORT_STAFF:
        await m.reply_text(text="Este usuário faz parte do meu Suporte!, Não posso banir o nosso!")
        return

    if user_id == Config.BOT_ID:
        await m.reply_text(
            text="""Você não pode gban nigga!
        Foda-se.......!"""
        )
        return

    if db.check_gban(user_id):
        db.remove_gban(user_id)
        await m.reply_text(text=f"Removido {user_first_name} da Lista Global de Banimento.")
        time = ((datetime.utcnow().strftime("%H:%M - %d-%m-%Y")),)
        LOGGER.info(f"{m.from_user.id} ungbanned {user_id} De {m.chat.id}")
        log_msg = f"""#UNGBAN
        <b>Originado de:</b> {m.chat.id}
        <b>Admin:</b> {(await mention_html(m.from_user.first_name, m.from_user.id))}
        <b>UnGbanned User:</b> {(await mention_html(user_first_name, user_id))}
        <b>UnGbanned User ID:</b> {user_id}
        <b>Carimbo do Evento:</b> {time}"""
        await c.send_message(MESSAGE_DUMP, log_msg)
        try:
            # Send message to user telling that he's ungbanned
            await c.send_message(
                user_id,
                text="Você foi removido da minha lista de banimento global..... Tenha cuidado, leva alguns segundos para adicioná-lo novamente...",
            )
        except Exception as ef:  # TODO: Improve Error Detection
            LOGGER.error(ef)
            LOGGER.error(format_exc())
        return

    await m.reply_text(text="Usuário não é gbanido!")
    return


@Gojo.on_message(
    command(["numgbans", "countgbans", "gbancount", "gbanscount"], sudo_cmd=True),
)
async def gban_count(_, m: Message):
    await m.reply_text(
        text=f"Número de pessoas gbanidas: <code>{(db.count_gbans())}</code>"
    )
    LOGGER.info(f"{m.from_user.id} counting gbans in {m.chat.id}")
    return


@Gojo.on_message(
    command(["gbanlist", "globalbanlist"], sudo_cmd=True),
)
async def gban_list(_, m: Message):
    banned_users = db.load_from_db()

    if not banned_users:
        await m.reply_text(text="Não há usuários gbanidos...!")
        return

    banfile = "Aqui estão todos os g4ys globalmente proibidos!\n\n"
    for user in banned_users:
        banfile += f"[x] <b>{Users.get_user_info(user['_id'])['name']}</b> - <code>{user['_id']}</code>\n"
        if user["reason"]:
            banfile += f"<b>Razão:</b> {user['reason']}\n"

    try:
        await m.reply_text(banfile)
    except MessageTooLong:
        with BytesIO(str.encode(await remove_markdown_and_html(banfile))) as f:
            f.name = "gbanlist.txt"
            await m.reply_document(
                document=f, caption="Aqui estão todos os g4ys globalmente proibidos!\n\n"
            )

    LOGGER.info(f"{m.from_user.id} gbanlist exportado em {m.chat.id}")

    return
