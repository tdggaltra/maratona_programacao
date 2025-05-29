// static/js/map.js - Versão definitivamente corrigida
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Map.js carregando...');
    
    // Carregar o SVG do mapa do Brasil
    fetch('/static/core/images/brazil-map.svg')
        .then(response => {
            console.log('📡 Resposta da fetch SVG:', response.status);
            if (!response.ok) {
                throw new Error(`Erro ao carregar o mapa: ${response.status} ${response.statusText}`);
            }
            return response.text();
        })
        .then(svgContent => {
            console.log('✅ SVG carregado com sucesso');
            document.getElementById('brazil-map').innerHTML = svgContent;
            
            // Após carregar o SVG, aplicar cores e interatividade
            setupMapInteractivity();
        })
        .catch(error => {
            console.error('❌ Erro ao carregar o mapa:', error);
            document.getElementById('brazil-map').innerHTML = 
                '<div class="alert alert-danger">Erro ao carregar o mapa do Brasil: ' + error.message + '. Por favor, recarregue a página.</div>';
        });
});

function setupMapInteractivity() {
    console.log('🔧 Configurando interatividade do mapa...');
    
    const svgElement = document.querySelector('#brazil-map svg');
    if (!svgElement) {
        console.error('❌ Elemento SVG não encontrado no DOM');
        return;
    }
    
    const stateElements = svgElement.querySelectorAll('path[id], circle[id]');
    console.log(`📍 Encontrados ${stateElements.length} elementos de estado no SVG`);
    
    const markers = document.querySelectorAll('.state-marker');
    console.log(`📍 Encontrados ${markers.length} marcadores HTML`);
    
    const tooltip = document.querySelector('.tooltip');
    if (!tooltip) {
        console.error('❌ Elemento tooltip não encontrado');
        return;
    }
    
    // Mapeamento de siglas de estados para regiões
    const stateRegions = {
        // Norte
        'AC': 'norte', 'AM': 'norte', 'RR': 'norte', 'AP': 'norte',
        'PA': 'norte', 'RO': 'norte', 'TO': 'norte',
        // Nordeste
        'MA': 'nordeste', 'PI': 'nordeste', 'CE': 'nordeste', 'RN': 'nordeste',
        'PB': 'nordeste', 'PE': 'nordeste', 'AL': 'nordeste', 'SE': 'nordeste',
        'BA': 'nordeste',
        // Centro-Oeste
        'MT': 'centro-oeste', 'MS': 'centro-oeste', 'GO': 'centro-oeste', 'DF': 'centro-oeste',
        // Sudeste
        'MG': 'sudeste', 'ES': 'sudeste', 'RJ': 'sudeste', 'SP': 'sudeste',
        // Sul
        'PR': 'sul', 'SC': 'sul', 'RS': 'sul'
    };
    
    // ========== CONFIGURAR ELEMENTOS SVG ==========
    stateElements.forEach(stateElement => {
        const stateId = stateElement.getAttribute('id');
        console.log(`🗺️ Processando elemento SVG: ${stateId}`);
        
        // Adicionar classe de região
        if (stateId in stateRegions) {
            stateElement.classList.add(stateRegions[stateId]);
        }
        
        // Encontrar o marcador correspondente
        const marker = document.querySelector(`#marker-${stateId}`);
        
        if (marker) {
            console.log(`✅ Marcador encontrado para ${stateId}`);
            
            // Adicionar classe de status baseado no marcador
            if (marker.classList.contains('completed')) {
                stateElement.classList.add('completed');
            } else if (marker.classList.contains('current')) {
                stateElement.classList.add('current');
            } else if (marker.classList.contains('available')) {
                stateElement.classList.add('available');
            } else {
                stateElement.classList.add('locked');
            }
            
            // IMPORTANTE: Só adiciona click se NÃO tem link HTML
            const hasHtmlLink = marker.querySelector('a');
            if (!hasHtmlLink && !marker.classList.contains('locked')) {
                console.log(`🔗 Adicionando click handler para ${stateId} (sem link HTML)`);
                stateElement.addEventListener('click', function() {
                    const challengeId = marker.getAttribute('data-challenge-id');
                    if (challengeId) {
                        console.log(`🚀 Redirecionando para: /challenges/${challengeId}/`);
                        window.location.href = `/challenges/${challengeId}/`;
                    }
                });
                stateElement.style.cursor = 'pointer';
            } else {
                console.log(`ℹ️ ${stateId} tem link HTML ou está bloqueado - não adiciona click handler`);
            }
            
            // Tooltip para elementos SVG
            stateElement.addEventListener('mouseenter', function(e) {
                showTooltip(e, marker, stateId, stateRegions);
                this.style.opacity = 0.8;
            });
            
            stateElement.addEventListener('mouseleave', function() {
                hideTooltip();
                this.style.opacity = '';
            });
            
        } else {
            console.log(`❌ Marcador NÃO encontrado para ${stateId}`);
            stateElement.classList.add('locked');
        }
    });
    
    // ========== CONFIGURAR MARCADORES HTML ==========
    markers.forEach(marker => {
        const stateId = marker.id.replace('marker-', '');
        console.log(`🏷️ Configurando marcador: ${stateId}`);
        
        // IMPORTANTE: Só adiciona click se NÃO tem link HTML
        const hasHtmlLink = marker.querySelector('a');
        if (!hasHtmlLink && !marker.classList.contains('locked')) {
            console.log(`🔗 Adicionando click handler para marcador ${stateId} (sem link HTML)`);
            marker.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const challengeId = this.getAttribute('data-challenge-id');
                if (challengeId) {
                    console.log(`🚀 Redirecionando para: /challenges/${challengeId}/`);
                    window.location.href = `/challenges/${challengeId}/`;
                }
            });
            marker.style.cursor = 'pointer';
        } else {
            console.log(`ℹ️ Marcador ${stateId} tem link HTML ou está bloqueado - não adiciona click handler`);
        }
        
        // Tooltip para marcadores
        marker.addEventListener('mouseenter', function(e) {
            showTooltip(e, marker, stateId, stateRegions);
        });
        
        marker.addEventListener('mouseleave', hideTooltip);
        
        marker.addEventListener('mousemove', function(e) {
            moveTooltip(e);
        });
    });
    
    console.log('✅ Configuração do mapa concluída');
}

// ========== FUNÇÕES AUXILIARES ==========
function showTooltip(e, marker, stateId, stateRegions) {
    const tooltip = document.querySelector('.tooltip');
    if (!tooltip) return;
    
    const stateName = marker.getAttribute('data-state-name');
    const order = marker.getAttribute('data-order');
    const region = stateRegions[stateId] || 'desconhecida';
    
    let status = 'Bloqueado';
    if (marker.classList.contains('completed')) {
        status = 'Completado';
    } else if (marker.classList.contains('current')) {
        status = 'Atual';
    } else if (marker.classList.contains('available')) {
        status = 'Disponível';
    }
    
    const content = `
        <strong>Estado:</strong> ${stateName}<br>
        <strong>Região:</strong> ${region.charAt(0).toUpperCase() + region.slice(1)}<br>
        <strong>Ordem:</strong> ${order}<br>
        <strong>Status:</strong> ${status}
    `;
    
    tooltip.innerHTML = content;
    tooltip.style.left = (e.pageX + 10) + 'px';
    tooltip.style.top = (e.pageY + 10) + 'px';
    tooltip.classList.add('visible');
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
    }
}

function moveTooltip(e) {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip && tooltip.classList.contains('visible')) {
        tooltip.style.left = (e.pageX + 10) + 'px';
        tooltip.style.top = (e.pageY + 10) + 'px';
    }
}