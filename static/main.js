// Dark / Light toggle with persistence
ction(){
const tog(fungle = document.getElementById('theme-toggle');
const current = localStorage.getItem('theme') || 'light';
if(current === 'dark') document.documentElement.setAttribute('data-theme','dark');
if(toggle){
toggle.addEventListener('click', ()=>{
const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
if(isDark){ document.documentElement.removeAttribute('data-theme'); localStorage.setItem('theme','light'); }
else{ document.documentElement.setAttribute('data-theme','