#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import os
import sys
import json
import asyncio
import socks
import shutil
import argparse
import json
from telethon.tl.types import User, UserFull
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetMessagesRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.types import MessageService, MessageEmpty
from telethon.tl.types import PeerUser, PeerChat
from telethon.errors.rpcerrorlist import AccessTokenExpiredError, RpcCallFailError
from telethon.tl.types import MessageMediaGeo, MessageMediaPhoto, MessageMediaDocument, MessageMediaContact
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeAudio, DocumentAttributeVideo, MessageActionChatEditPhoto
from rich.console import Console
from rich.table import Table
from rich.text import Text
import asyncio
import argparse
import keyboard
from telethon.errors import AccessTokenExpiredError, AccessTokenInvalidError  # Import specific errors

API_ID = ################################################################
API_HASH = '################################################################'
HISTORY_DUMP_STEP = 200
LOOKAHEAD_STEP_COUNT = 0
all_chats = {}
all_users = {}
messages_by_chat = {}
base_path = ''
console = Console()

def serialize_telegram_object(obj):
    if isinstance(obj, (User, UserFull)):
        return {key: serialize_telegram_object(value) for key, value in obj.__dict__.items() if not key.startswith('_')}
    elif isinstance(obj, (list, tuple)):
        return [serialize_telegram_object(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_telegram_object(value) for key, value in obj.items()}
    elif hasattr(obj, '__dict__'):
        return serialize_telegram_object(obj.__dict__)
    else:
        return obj


def print_bot_info(bot_info):
    print(f"ID: {bot_info.id}")
    print(f"Name: {bot_info.first_name}")
    print(f"Username: @{bot_info.username} - https://t.me/{bot_info.username}")


def print_user_info(user_full):
    print("="*20 + "\n[DiamondDumper] - NEW USER DETECTED")
    
    user_info = serialize_telegram_object(user_full)
    
    if 'user' in user_info:
        user = user_info['user']
    else:
        user = user_info

    print(f"ID: {user.get('id', 'Unknown')}")
    print(f"First name: {user.get('first_name', 'Unknown')}")
    print(f"Last name: {user.get('last_name', 'Unknown')}")
    if 'username' in user:
        print(f"[DiamondDumper] - Username: @{user['username']} - https://t.me/{user['username']}")
    else:
        print("[DiamondDumper] - User has no username")
    
    print(f"[DiamondDumper] - Bio: {user_info.get('about', 'No bio')}")
    print(f"[DiamondDumper] - Common chats count: {user_info.get('common_chats_count', 'Unknown')}")
    
    if 'status' in user:
        status = user['status']
        if isinstance(status, dict) and 'was_online' in status:
            print(f"[DiamondDumper] - Last seen: {status['was_online']}")


def save_user_info(user_full):
    if hasattr(user_full, 'user'):
        user = user_full.user
    else:
        user = user_full

    user_id = str(getattr(user, 'id', 'unknown'))
    username = getattr(user, 'username', None) or 'unknown'
    
    user_dir = os.path.join(base_path, user_id)
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
        
    user_media_dir = os.path.join(base_path, user_id, 'media')
    
    # Create media directory if it doesn't exist
    if not os.path.exists(user_media_dir):
        os.mkdir(user_media_dir)
    
    # Serialize the UserFull object
    user_info = serialize_telegram_object(user_full)

    # Add signature to the user_info
    user_info['signature'] = {
        "source": "DiamondDumper",
        "repository": "https://github.com/L33TSP3AK",
        "discussion": "https://github.com/L33TSP3AK/L33TSP3AK/discussions"
    }
    
    # Determine the filename based on username or ID
    filename = f"{username if username else user_id}_DiamondDumper.json"
    
    # Save the serialized data to a JSON file in pretty format
    with open(os.path.join(user_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4, default=str)  # Set indent to 4 for pretty format



async def save_user_photos(bot, user_full):
    if hasattr(user_full, 'user'):
        user = user_full.user
    else:
        user = user_full

    user_id = str(getattr(user, 'id', getattr(user_full, 'id', 'unknown')))
    user_dir = os.path.join(base_path, user_id)
    
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)

    try:
        result = await safe_api_request(bot(GetUserPhotosRequest(user_id=int(user_id), offset=0, max_id=0, limit=100)), 'get user photos')
        if not result:
            print(f"[DiamondDumper] - No photos found for user {user_id}")
            return
        
        for photo in result.photos:
            print(f"[DiamondDumper] - Saving photo {photo.id}...")
            file_path = os.path.join(user_dir, f'{photo.id}.jpg')
            await safe_api_request(bot.download_file(photo, file_path), 'download user photo')
    except Exception as e:
        print(f"[DiamondDumper] - Error saving user photos: {str(e)}")


async def safe_api_request(coroutine, comment):
    result = None
    try:
        result = await coroutine
    except RpcCallFailError as e:
        print(f"[DiamondDumper] - Telegram API error, {comment}: {str(e)}")
    except Exception as e:
        print(f"[DiamondDumper] - Some error, {comment}: {str(e)}")
    return result


async def save_user_photos(bot, user_full):
    if hasattr(user_full, 'user') and hasattr(user_full.user, 'id'):
        user_id = str(user_full.user.id)
    else:
        print("[DiamondDumper] - Unable to find user ID in UserFull object")
        return

    user_dir = os.path.join(base_path, user_id)
    
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)

    try:
        result = await safe_api_request(bot(GetUserPhotosRequest(user_id=int(user_id), offset=0, max_id=0, limit=100)), 'get user photos')
        if not result:
            print(f"[DiamondDumper] - No photos found for user {user_id}")
            return
        
        for photo in result.photos:
            print(f"Saving photo {photo.id}...")
            file_path = os.path.join(user_dir, f'{photo.id}.jpg')
            await safe_api_request(bot.download_file(photo, file_path), 'download user photo')
    except Exception as e:
        print(f"[DiamondDumper] - Error saving user photos: {str(e)}")


async def save_media_photo(bot, chat_id, photo):
    user_media_dir = os.path.join(base_path, chat_id, 'Photos')
    await safe_api_request(bot.download_file(photo, os.path.join(user_media_dir, f'{photo.id}.jpg')), 'download media photo')


def get_document_filename(document):
    for attr in document.attributes:
        if isinstance(attr, DocumentAttributeFilename):
            return attr.file_name
        # voice & round video
        if isinstance(attr, DocumentAttributeAudio) or isinstance(attr, DocumentAttributeVideo):
            return f'{document.id}.{document.mime_type.split("/")[1]}'


async def save_media_document(bot, chat_id, document):
    user_media_dir = os.path.join(base_path, chat_id, 'Documents')
    filename = os.path.join(user_media_dir, get_document_filename(document))
    if os.path.exists(filename):
        old_filename, extension = os.path.splitext(filename)
        filename = f'{old_filename}_{document.id}{extension}'
    await safe_api_request(bot.download_file(document, filename), 'download file')
    return filename


def remove_old_text_history(chat_id):
    user_dir = os.path.join(base_path, str(chat_id))
    history_filename = os.path.join(user_dir, f'Diamond_{chat_id}_history.txt')
    if os.path.exists(history_filename):
        print(f"[DiamondDumper] - Removing old history of {chat_id}...")
        os.remove(history_filename)


def save_text_history(chat_id, messages):
    user_dir = os.path.join(base_path, str(chat_id))
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
        
    history_filename = os.path.join(user_dir, f'Diamond_{chat_id}_history.txt')
    
    # Append messages to the text file
    with open(history_filename, 'a', encoding='utf-8') as text_file:
        text_file.write('\n'.join(messages) + '\n')
        
        # Add signature at the end of the file
        text_file.write("\n---\n")
        text_file.write("Source: DiamondDumper\n")
        text_file.write("Repository: https://github.com/L33TSP3AK\n")
        text_file.write("Discussion: https://github.com/L33TSP3AK/L33TSP3AK/discussions\n")
        text_file.write("---\n")


def save_chats_text_history():
    for m_chat_id, messages_dict in messages_by_chat.items():
        console.print(f"[bold blue][DiamondDumper] - Saving history of {m_chat_id} as a text...[/bold blue]")
        new_messages = messages_dict['buf']
        save_text_history(m_chat_id, new_messages)
        messages_by_chat[m_chat_id]['history'] += new_messages
        messages_by_chat[m_chat_id]['buf'] = []


def get_chat_id(message, bot_id):
    m = message
    m_chat_id = 0
    if isinstance(m.peer_id, PeerUser):
        if not m.to_id or not m.from_id:
            m_chat_id = str(m.peer_id.user_id)
        else:
            if m.from_id and int(m.from_id.user_id) == int(bot_id):
                m_chat_id = str(m.to_id.user_id)
            else:
                m_chat_id = str(m.from_id)
    elif isinstance(m.peer_id, PeerChat):
        m_chat_id = str(m.peer_id.chat_id)

    return m_chat_id


def get_from_id(message, bot_id):
    m = message
    from_id = 0
    if isinstance(m.peer_id, PeerUser):
        if not m.from_id:
            from_id = str(m.peer_id.user_id)
        else:
            from_id = str(m.from_id.user_id)
    elif isinstance(m.peer_id, PeerChat):
        from_id = str(m.from_id.user_id)

    return from_id

async def process_message(bot, m, empty_message_counter=0):
    m_chat_id = get_chat_id(m, bot.id)
    m_from_id = get_from_id(m, bot.id)

    is_from_user = m_chat_id == m_from_id

    if isinstance(m, MessageEmpty):
        empty_message_counter += 1
        return True
    elif empty_message_counter:
        console.print(f'[bold yellow][DiamondDumper] - Empty messages x{empty_message_counter}[/bold yellow]')
        empty_message_counter = 0

    message_text = ''
    
    # Handle different message types and media
    if m.media:
        if isinstance(m.media, MessageMediaGeo):
            message_text = f'[DiamondDumper] - Geoposition: {m.media.geo.long}, {m.media.geo.lat}'
        elif isinstance(m.media, MessageMediaPhoto):
            await save_media_photo(bot, m_chat_id, m.media.photo)
            message_text = f'[DiamondDumper] - Photo: media/{m.media.photo.id}.jpg'
        elif isinstance(m.media, MessageMediaContact):
            message_text = f'[DiamondDumper] - Vcard: phone {m.media.phone_number}, {m.media.first_name} {m.media.last_name}, rawdata {m.media.vcard}'
        elif isinstance(m.media, MessageMediaDocument):
            full_filename = await save_media_document(bot, m_chat_id, m.media.document)
            filename = os.path.split(full_filename)[-1]
            message_text = f'[DiamondDumper] - Document: media/{filename}'
        else:
            console.print(m.media)
    else:
        if isinstance(m.action, MessageActionChatEditPhoto):
            await save_media_photo(bot, m_chat_id, m.action.photo)
            message_text = f'[DiamondDumper] - Photo of chat was changed: media/{m.action.photo.id}.jpg'
        elif m.action:
            message_text = str(m.action)

    if m.message:
        message_text = '\n'.join([message_text, m.message]).strip()

    text = f'[{m.id}][{m_from_id}][{m.date}] {message_text}'
    console.print(Text(text, style="cyan"))

    if m_chat_id not in messages_by_chat:
        messages_by_chat[m_chat_id] = {'buf': [], 'history': []}

    messages_by_chat[m_chat_id]['buf'].append(text)

    if is_from_user and m_from_id and m_from_id not in all_users:
        try:
            full_user = await bot(GetFullUserRequest(int(m_from_id)))
            
            # Extract user ID safely
            user_id = str(full_user.user.id) if hasattr(full_user, 'user') and hasattr(full_user.user, 'id') else str(m_from_id)
            
            console.print(f"[bold magenta]Processing user: {user_id}[/bold magenta]")
            print_user_info(full_user)
            save_user_info(full_user)
            remove_old_text_history(user_id)
            await save_user_photos(bot, full_user)
            all_users[user_id] = full_user
        except Exception as e:
            console.print(f"[red][DiamondDumper] - Error processing user {m_from_id}: {str(e)}[/red]")
            console.print(f"[red][DiamondDumper] - Full user object: {full_user}[/red]")

async def get_chat_history(bot, from_id=0, to_id=0, chat_id=None, lookahead=0):
    print(f'[DiamondDumper] - Dumping history from {from_id} to {to_id}...')
    messages = await bot(GetMessagesRequest(range(to_id, from_id)))
    empty_message_counter = 0
    history_tail = True
    for m in messages.messages:
        is_empty = await process_message(bot, m, empty_message_counter)
        if is_empty:
            empty_message_counter += 1

    if empty_message_counter:
        print(f'[DiamondDumper] - Empty messages x{empty_message_counter}')
        history_tail = True

    save_chats_text_history()
    if not history_tail:
        return await get_chat_history(bot, from_id+HISTORY_DUMP_STEP, to_id+HISTORY_DUMP_STEP, chat_id, lookahead)
    else:
        if lookahead:
            return await get_chat_history(bot, from_id+HISTORY_DUMP_STEP, to_id+HISTORY_DUMP_STEP, chat_id, lookahead-1)
        else:
            print('[DiamondDumper] - History was fully dumped.')
            return None

async def bot_auth(bot_token, proxy=None):
    global base_path
    bot_id = bot_token.split(':')[0]
    base_path = bot_id
    
    # Create or rename directory for bot sessions
    if os.path.exists(base_path):
        import time
        new_path = f'{base_path}_{str(int(time.time()))}'
        os.rename(base_path, new_path)
        os.mkdir(base_path)
        
        # Check if the session file exists before copying
        session_file = f'{new_path}/{base_path}.session'
        if os.path.exists(session_file):
            shutil.copyfile(session_file, f'{base_path}/{base_path}.session')
        else:
            print(f"[DiamondDumper] - Session file {session_file} does not exist. A new one will be created.")
    else:
        os.mkdir(base_path)

    try:
        # Start the Telegram client with the provided token
        bot = await TelegramClient(os.path.join(base_path, bot_id), API_ID, API_HASH, proxy=proxy).start(bot_token=bot_token)
        bot.id = bot_id
    except AccessTokenInvalidError:
        print("[bold red][DiamondDumper] - Display Error: Bottoken Issue - Try Again[/bold red]")
        return None, None  # Return None to indicate failure
    except AccessTokenExpiredError:
        print("[DiamondDumper] - Token has expired!")
        sys.exit()

    me = await bot.get_me()
    print_bot_info(me)
    user_full = await bot(GetFullUserRequest(me.id))
    all_users[me.id] = user_full

    user_info = me.to_dict()
    user_info['token'] = bot_token

    with open(os.path.join(bot_id, 'bot.json'), 'w') as bot_info_file:
        json.dump(user_info, bot_info_file)

    return bot, me



async def typing_animation(text, delay=0.005):
    """Simulates a typing animation for the given text."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        await asyncio.sleep(delay)
    print()  # Move to the next line after finishing



async def loading_animation(message):
    """Display a loading animation while transitioning to listening mode."""
    spinner = ["|", "/", "-", "\\"]
    while True:
        for frame in spinner:
            console.print(f"[bold yellow]{message} {frame}[/bold yellow]", end="\r")
            await asyncio.sleep(0.1)  # Adjust the speed of the spinner


async def main():
    welcome_message = "[DiamondDumper] - Check out my GitHub page: github.com/L33tSp3ak!\nLeave a comment https://github.com/L33TSP3AK/L33TSP3AK/discussions"
    await typing_animation(welcome_message)

    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Telegram bot token(s) to check (separate multiple tokens with semicolons)")
    parser.add_argument("--listen-only", help="Don't dump all the bot history", action="store_true")
    parser.add_argument("--lookahead", help="Additional cycles to skip empty messages",
                        default=LOOKAHEAD_STEP_COUNT, type=int)
    parser.add_argument("--tor", help="enable Tor socks proxy", action="store_true")
    args = parser.parse_args()

    proxy = (socks.SOCKS5, '127.0.0.1', 9050) if args.tor else None

    if not args.token:
        bot_tokens = input("[DiamondDumper] - Enter token bot(s) (separate multiple tokens with semicolons): ").split(';')
    else:
        bot_tokens = args.token.split(';')

    authenticated_bots = []

    # First, authenticate and dump all bots
    for i, bot_token in enumerate(bot_tokens, 1):
        bot_token = bot_token.strip()
        console.print(f"\n[bold cyan]Processing Bot Token {i}/{len(bot_tokens)}[/bold cyan]")
        console.print(f"Token: {bot_token[:10]}...")

        try:
            # Authenticate the bot
            bot, bot_info = await bot_auth(bot_token, proxy)
            
            # Check if authentication was successful
            if bot is None:
                console.print(f"[bold red]Bot authentication failed for token {i}. Skipping...[/bold red]")
                continue

            console.print(f"[bold green]Successfully authenticated bot: @{bot_info.username}[/bold green]")
            console.print(f"ID: {bot_info.id}")
            console.print(f"Name: {bot_info.first_name}")
            console.print(f"Username: @{bot_info.username} - https://t.me/{bot_info.username}")

            authenticated_bots.append((bot, bot_info))

            if not args.listen_only:
                console.print(f"[bold blue]Dumping history for bot {i}/{len(bot_tokens)}...[/bold blue]")
                await get_chat_history(bot, from_id=HISTORY_DUMP_STEP, to_id=0, lookahead=args.lookahead)
            else:
                console.print("[yellow]Listen-only mode enabled. Skipping dump.[/yellow]")

        except PermissionError as e:
            console.print(f"[bold red]Error processing token {i}: Access denied[/bold red]")
            console.print(f"[red]Details: {str(e)}[/red]")
            console.print("[yellow]Waiting 3 seconds before skipping to the next token...[/yellow]")
            await asyncio.sleep(3)
            continue

        except Exception as e:
            console.print(f"[bold red]Unexpected error processing token {i}[/bold red]")
            console.print(f"[red]Details: {str(e)}[/red]")
            console.print("[yellow]Waiting 3 seconds before skipping to the next token...[/yellow]")
            await asyncio.sleep(3)
            continue

        # Add a delay between processing tokens to avoid rate limiting
        if i < len(bot_tokens):
            console.print("[cyan]Waiting 5 seconds before processing the next token...[/cyan]")
            await asyncio.sleep(5)

    console.print("\n[bold green]All tokens processed and dumped![/bold green]")

    # Now enter listening mode for each bot
    for i, (bot, bot_info) in enumerate(authenticated_bots, 1):
        console.print(f"\n[bold cyan]Entering listening mode for Bot {i}/{len(authenticated_bots)} (@{bot_info.username})[/bold cyan]")

        @bot.on(events.NewMessage)
        async def save_new_user_history(event):
            user = event.message.sender
            chat_id = event.message.chat_id
            if chat_id not in all_chats:
                all_chats[chat_id] = event.message.input_chat
                messages_by_chat[chat_id] = {'history': [], 'buf': []}
                console.print('=' * 20 + f'\n[DiamondDumper] - NEW CHAT DETECTED: {chat_id}')
                if user.id not in all_users:
                    print_user_info(user)
                    save_user_info(user)
                    await save_user_photos(bot, user)

            await process_message(bot, event.message)

        console.print('[bold blue][DiamondDumper] - Press Ctrl+C to STOP listening for new messages...[/bold blue]')
        
        # Start loading animation in background
        loading_message = f"[DiamondDumper] - Now in 'Listening Mode' for Bot {i}/{len(authenticated_bots)}...."
        loading_task = asyncio.create_task(loading_animation(loading_message))

        # Final message displayed in rich text after loading
        final_message = Text.from_markup(
            f"""
            [bold magenta][DiamondDumper] - Bot {i}/{len(authenticated_bots)} (@{bot_info.username})[/bold magenta]
            This mode - As long as it's open, will continue to listen for new traffic and messages from this bot and document them as they come in...
            Press Ctrl+C to STOP listening for new messages and move to the next bot... 
            Press Ctrl+T to Enter A New Token - Leaving Listening Mode....

            [bold green]Thanks for using Diamond Dumper.
            [link=https://t.me/DiamondDumper]https://t.me/DiamondDumper[/link][/bold green]
            """
        )
        
        await asyncio.sleep(1)  # Optional delay before showing final message
        loading_task.cancel()  # Cancel the spinner task
        console.print(final_message)

        try:
            while True:
                await asyncio.sleep(1)  # Replace with actual bot logic
        except KeyboardInterrupt:
            console.print(f"[bold red]Stopped listening for new messages for Bot {i}/{len(authenticated_bots)}.[/bold red]")

    console.print("\n[bold green]Finished listening for all bots![/bold green]")

if __name__ == '__main__':
    asyncio.run(main())