
document.addEventListener('DOMContentLoaded', function(){
  const robot = document.getElementById('robot');
  const chat = document.getElementById('chatModal');
  const closeChat = document.getElementById('closeChat');
  const chatBody = document.getElementById('chatBody');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  robot.addEventListener('click', () => {
    chat.style.display = 'flex';
    chatInput.focus();
  });
  closeChat.addEventListener('click', ()=> chat.style.display = 'none');

  function appendUser(msg){
    const d = document.createElement('div'); d.className='user-msg'; d.textContent = msg;
    chatBody.appendChild(d); chatBody.scrollTop = chatBody.scrollHeight;
  }
  function appendBot(msg){
    const d = document.createElement('div'); d.className='bot-msg'; d.textContent = msg;
    chatBody.appendChild(d); chatBody.scrollTop = chatBody.scrollHeight;
  }

  sendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', function(e){ if(e.key==='Enter'){ sendMessage(); } });

  function sendMessage(){
    const text = chatInput.value.trim();
    if(!text) return;
    appendUser(text);
    chatInput.value='';
    fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: text})
    }).then(r=>r.json()).then(data=>{
      appendBot(data.reply);
    }).catch(err=>{
      appendBot("Sorry, chat failed. Try again.")
    });
  }
});

