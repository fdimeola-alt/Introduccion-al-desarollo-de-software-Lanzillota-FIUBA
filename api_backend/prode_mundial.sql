CREATE DATABASE IF NOT EXISTS prode_mundial;
use prode_mundial;

CREATE TABLE IF NOT EXISTS partidos (
    id  INT AUTO_INCREMENT PRIMARY KEY,
    equipo_local VARCHAR(255) NOT NULL,
    equipo_visitante VARCHAR(255) NOT NULL,
    fecha DATE NOT NULL,
    fase ENUM('grupos', 'desicesiavos', 'octavos', 'cuartos', 'semifinales', 'final') NOT NULL,
    gol_local INT DEFAULT NULL,
    gol_visitante INT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    CONSTRAINT uq_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS predicciones (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    id_partido      INT NOT NULL,
    id_usuario      INT NOT NULL,
    gol_local     INT NOT NULL,
    gol_visitante INT NOT NULL,
    CONSTRAINT fk_partido FOREIGN KEY (id_partido) REFERENCES partidos(id) ON DELETE CASCADE,
    CONSTRAINT fk_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT uq_pred    UNIQUE (id_partido, id_usuario)
);

INSERT INTO partidos (equipo_local, equipo_visitante, fecha, fase) VALUES
('Qatar', 'Ecuador', '2022-11-20', 'grupos'),
('Inglaterra', 'Irán', '2022-11-21', 'grupos'),
('Senegal', 'Países Bajos', '2022-11-21', 'grupos'),
('Estados Unidos', 'Gales', '2022-11-21', 'grupos');

INSERT INTO usuarios (email, nombre) VALUES
('john.doe@example.com', 'John Doe'),
('juan.gomez@example.com', 'Juan gomez'),
('maria.gonzalez@example.com', 'Maria Gonzalez'),
('pedro.perez@example.com', 'Pedro Perez'),
('laura.lopez@example.com', 'Laura Lopez');

