using UnityEngine;
using UnityEngine.InputSystem; 

public class CameraDepthTravel : MonoBehaviour
{
    [Header("Movimiento (W/S)")]
    public float speed = 10f;
    public float minZ = -50f;
    public float maxZ = 100f;

    [Header("Rango de Cámara (A/D)")]
    public float farPlaneChangeSpeed = 50f; // Qué tan rápido cambia el far plane
    [Range(0.01f, 5f)] public float nearPlane = 0.3f;
    public float farPlane = 1000f;

    private Camera cam;

    void Start()
    {
        cam = GetComponent<Camera>();
    }

    void Update()
    {
        if (Keyboard.current == null) return;

        // 1. MOVIMIENTO (W / S)
        float moveInput = 0;
        if (Keyboard.current.wKey.isPressed || Keyboard.current.upArrowKey.isPressed)
            moveInput = 1f;
        else if (Keyboard.current.sKey.isPressed || Keyboard.current.downArrowKey.isPressed)
            moveInput = -1f;

        float newZ = transform.position.z + (moveInput * speed * Time.deltaTime);
        newZ = Mathf.Clamp(newZ, minZ, maxZ);
        transform.position = new Vector3(transform.position.x, transform.position.y, newZ);

        // 2. CONTROL DEL FAR PLANE (A / D)
        if (Keyboard.current.aKey.isPressed)
            farPlane -= farPlaneChangeSpeed * Time.deltaTime;
        else if (Keyboard.current.dKey.isPressed)
            farPlane += farPlaneChangeSpeed * Time.deltaTime;

        // Limitar el far plane para que no sea menor que el near plane
        farPlane = Mathf.Max(farPlane, nearPlane + 1f);

        // 3. APLICAR A LA CÁMARA
        if (cam != null)
        {
            cam.nearClipPlane = nearPlane;
            cam.farClipPlane = farPlane;
        }
    }
}