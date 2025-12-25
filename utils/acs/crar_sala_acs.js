import { CommunicationIdentityClient } from "@azure/communication-identity";
import { RoomsClient, KnownRole } from "@azure/communication-rooms";

import dotenv from "dotenv";
dotenv.config();


// 🔐 Connection string de tu recurso ACS
const connectionString = process.env.ACS_CONNECTION_STRING;


async function crearSalaConUsuarios() {
  // Crear cliente de identidades
  const identityClient = new CommunicationIdentityClient(connectionString);
  const roomsClient = new RoomsClient(connectionString);

  // Crear dos usuarios: host y visitante
  const { communicationUserId: hostId } = await identityClient.createUser();
  const { communicationUserId: visitanteId } = await identityClient.createUser();

  // Generar tokens de acceso
  const { token: tokenHost } = await identityClient.getToken({ communicationUserId: hostId }, ["voip"]);
  const { token: tokenVisitante } = await identityClient.getToken({ communicationUserId: visitanteId }, ["voip"]);

  console.log("✅ Usuarios creados:");
  console.log("Host ID:", hostId);
  console.log("Visitante ID:", visitanteId);

  // Crear sala (room)
  const startsAt = new Date(Date.now() + 1 * 60 * 1000); // comienza en 1 minuto
  const endsAt = new Date(Date.now() + 60 * 60 * 1000); // dura 1 hora

  const { id: roomId } = await roomsClient.createRoom({
    validFrom: startsAt,
    validUntil: endsAt,
  });

  console.log("✅ Sala creada:", roomId);

  // Agregar participantes a la sala
  await roomsClient.addOrUpdateParticipants(roomId, [
    { communicationIdentifier: { communicationUserId: hostId }, role: KnownRole.Presenter },
    { communicationIdentifier: { communicationUserId: visitanteId }, role: KnownRole.Attendee },
  ]);

  console.log("✅ Participantes añadidos");

  // Mostrar tokens para usarlos en la UI
  console.log("\n🔗 Info de conexión:");
  console.log("Room ID:", roomId);
  console.log("Host Token:", tokenHost);
  console.log("Visitante Token:", tokenVisitante);
}

crearSalaConUsuarios().catch(console.error);
