plugins {
    kotlin("jvm") version "2.1.21"
    kotlin("plugin.serialization") version "2.1.21"
    application
}

group = "com.digestagent"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    // Koog AI Framework (Real JetBrains framework)
    implementation("ai.koog:koog-agents:0.5.0")
    
    // Kotlin Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-jdk8:1.7.3")
    
    // Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
    
    // HTTP Client
    implementation("io.ktor:ktor-client-core:2.3.5")
    implementation("io.ktor:ktor-client-cio:2.3.5")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.5")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.5")
    implementation("io.ktor:ktor-client-logging:2.3.5")
    
    // Logging
    implementation("org.slf4j:slf4j-api:2.0.9")
    implementation("ch.qos.logback:logback-classic:1.4.11")
    
    // Environment Variables
    implementation("io.github.cdimascio:dotenv-kotlin:6.4.1")
    
    // HTTP Client for Telegram
    implementation("io.ktor:ktor-client-core:2.3.5")
    implementation("io.ktor:ktor-client-cio:2.3.5")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.5")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.5")
    
    // Testing
    testImplementation(kotlin("test"))
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    testImplementation("io.mockk:mockk:1.13.8")
}

application {
    mainClass.set("com.digestagent.MainKt")
}

tasks.register<JavaExec>("debugProductHunt") {
    classpath = sourceSets["main"].runtimeClasspath
    mainClass.set("com.digestagent.DebugProductHuntKt")
}

tasks.register<JavaExec>("testTelegram") {
    classpath = sourceSets["main"].runtimeClasspath
    mainClass.set("com.digestagent.TelegramTestKt")
    args = if (project.hasProperty("chatId")) {
        listOf(project.property("chatId").toString())
    } else {
        emptyList()
    }
}

tasks.test {
    useJUnitPlatform()
}

kotlin {
    jvmToolchain(17)
}