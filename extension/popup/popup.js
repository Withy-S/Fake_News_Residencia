document.addEventListener("DOMContentLoaded", function() {
  
  const percentElement = document.getElementById("fake-percent");

  let alvo = 50;   // Valor da IA que queremos atingir
  let atual = 0;   // A água começa no zero
  let waveX = 0;   // Posição horizontal infinita da onda
  
  function animarAgua() {
    
    // 1. O ENCHIMENTO (Contador até ao alvo)
    if (atual < alvo) {
      atual += 0.5; // Velocidade da água subindo
      if (atual > alvo) atual = alvo; // Trava quando atinge o alvo
    }

    // 2. O FLUXO DA ONDA (Eixo X)
    // Subtraímos 1 pixel a cada pulso do clock. A onda anda para a esquerda para sempre!
    waveX -= 1; 

    // 3. A CALIBRAÇÃO DO SENSOR (Eixo Y)
    // Lembra da caixa invisível? O fundo começa no pixel 30 (0%) e sobe até ao pixel -6 (100%).
    // Esta fórmula matemática simples (Offset e Ganho) resolve isso perfeitamente:
    let yPos = 30 - (atual * 0.36); 

    // 4. ATUALIZAR A TELA
    percentElement.textContent = Math.floor(atual) + "%";
    
    // 5. INJETAR COORDENADAS NO CSS
    percentElement.style.setProperty("--wave-x", waveX + "px");
    percentElement.style.setProperty("--fill-y", yPos + "px");

    // Loop eterno no ritmo do monitor (60Hz)
    requestAnimationFrame(animarAgua);
  }

  // Aciona o motor!
  animarAgua();

});