# 🌐 Guía Completa de Configuración de Proxies

## ¿Por qué usar Proxies?

Los proxies te permiten:
- **Distribuir tráfico** entre diferentes IPs
- **Evitar bloqueos** del WAF por múltiples conexiones desde la misma IP
- **Abrir más instancias** sin ser detectado
- **Simular usuarios** desde diferentes ubicaciones

## 🔧 Configuración Paso a Paso

### 1. **Obtener Proxies**

#### **Proxies Gratuitos (Limitados)**
- **FreeProxyList**: https://www.freeproxylist.net/
- **ProxyScrape**: https://proxyscrape.com/
- **HideMyName**: https://hidemy.name/es/proxy-list/

#### **Proxies Premium (Recomendados)**
- **Bright Data**: https://brightdata.com/
- **ProxyMesh**: https://proxymesh.com/
- **SmartProxy**: https://smartproxy.com/

### 2. **Configurar el Archivo proxies.txt**

Edita el archivo `proxies.txt` con tus proxies:

```
# Proxies HTTP (más comunes)
103.152.112.145:80
45.77.56.123:8080
167.99.83.205:8080

# Proxies con autenticación
192.168.1.100:8080:usuario:contraseña
10.0.0.1:3128:mi_usuario:mi_password

# Proxies SOCKS5 (mejor para evasión)
127.0.0.1:1080
192.168.1.1:1080
```

### 3. **Formato de Proxies**

#### **Sin Autenticación:**
```
ip:puerto
192.168.1.100:8080
```

#### **Con Autenticación:**
```
ip:puerto:usuario:contraseña
192.168.1.100:8080:mi_usuario:mi_password
```

## 🚀 Uso en la Aplicación

### **Paso 1: Cargar Proxies**
1. Ejecuta `instancesIU_advanced.py`
2. Haz clic en **"Cargar Lista de Proxies"**
3. Verifica que se cargaron correctamente

### **Paso 2: Probar Conexión**
1. Haz clic en **"Probar Conexión de Proxies"**
2. Espera a que se prueben los primeros 3 proxies
3. Verifica cuáles funcionan

### **Paso 3: Activar Proxies**
1. Marca la casilla **"Usar Proxies"**
2. Configura tus instancias normalmente
3. Ejecuta el script

## 📊 Ventajas de Usar Proxies

### **Sin Proxies:**
- ❌ Todas las instancias desde la misma IP
- ❌ Fácil detección por WAF
- ❌ Limitado a 2-3 instancias máximo
- ❌ Bloqueos frecuentes

### **Con Proxies:**
- ✅ Cada instancia desde IP diferente
- ✅ Difícil detección por WAF
- ✅ Puedes abrir 10+ instancias
- ✅ Menos bloqueos

## 🔍 Tipos de Proxies

### **HTTP/HTTPS Proxies**
- **Ventajas**: Fáciles de configurar, amplia compatibilidad
- **Desventajas**: Pueden ser detectados más fácilmente
- **Uso**: Ideal para la mayoría de casos

### **SOCKS5 Proxies**
- **Ventajas**: Mejor para evasión, más seguros
- **Desventajas**: Configuración más compleja
- **Uso**: Para casos que requieren máxima evasión

### **Proxies Residenciales**
- **Ventajas**: IPs reales de usuarios, muy difíciles de detectar
- **Desventajas**: Más caros, velocidad variable
- **Uso**: Para casos críticos

## ⚙️ Configuración Avanzada

### **Rotación de Proxies**
El sistema automáticamente:
- Selecciona un proxy aleatorio para cada instancia
- Evita usar el mismo proxy dos veces seguidas
- Maneja proxies que fallan

### **Configuración de Timeouts**
```python
# En el código, puedes ajustar:
timeout=5  # Segundos para probar conexión
```

### **Filtrado de Proxies**
```python
# Solo proxies que funcionan:
working_proxies = [proxy for proxy in proxy_list if test_proxy(proxy)]
```

## 🛠️ Solución de Problemas

### **"No se cargaron proxies"**
- Verifica que el archivo `proxies.txt` existe
- Revisa el formato de los proxies
- Asegúrate de que no hay líneas vacías

### **"Proxies no funcionan"**
- Prueba los proxies manualmente
- Verifica que no estén bloqueados
- Considera usar proxies premium

### **"Conexión lenta"**
- Usa proxies más cercanos geográficamente
- Evita proxies gratuitos sobrecargados
- Considera proxies dedicados

## 📈 Mejores Prácticas

### **Para Máxima Evasión:**
1. **Usa proxies residenciales** cuando sea posible
2. **Rota proxies** entre sesiones
3. **Combina con delays variables**
4. **Activa modo sigiloso**
5. **Usa diferentes User-Agents**

### **Para Mejor Rendimiento:**
1. **Prueba proxies** antes de usar
2. **Usa proxies cercanos** geográficamente
3. **Evita proxies sobrecargados**
4. **Monitorea la velocidad**

## 💡 Consejos Adicionales

### **Configuración Óptima:**
- **5-10 proxies** para 3-5 instancias
- **Proxies de diferentes países** para mayor diversidad
- **Proxies con buena velocidad** (>1MB/s)
- **Proxies con baja latencia** (<200ms)

### **Monitoreo:**
- Revisa logs de conexión
- Prueba proxies regularmente
- Reemplaza proxies que fallan
- Mantén una lista de respaldo

## 🔒 Consideraciones de Seguridad

- **No uses proxies gratuitos** para datos sensibles
- **Verifica la reputación** del proveedor
- **Usa HTTPS** cuando sea posible
- **No compartas** tus proxies con otros

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en la consola
2. Prueba proxies manualmente
3. Verifica la configuración
4. Considera proxies premium
