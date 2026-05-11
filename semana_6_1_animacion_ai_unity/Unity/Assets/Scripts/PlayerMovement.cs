using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody))]
public class PlayerMovement : MonoBehaviour
{
    [Header("Movement")]
    public float speed = 5f;
    public float rotationSpeed = 360f;

    [Header("Bounds")]
    public float boundaryLimit = 23f;   // margin inside the 25-unit plane edge
    public float returnSpeed  = 4f;     // speed while auto-returning
    public float returnThreshold = 4f;  // distance to center to stop auto-return

    bool _returning = false;
    Rigidbody _rb;

    void Start()
    {
        _rb = GetComponent<Rigidbody>();
        _rb.constraints = RigidbodyConstraints.FreezeRotation;
    }

    void FixedUpdate()
    {
        Vector3 pos = _rb.position;

        // ── Check if player is outside the walkable area ──────────
        bool outOfBounds = Mathf.Abs(pos.x) > boundaryLimit ||
                           Mathf.Abs(pos.z) > boundaryLimit;

        if (outOfBounds && !_returning)
        {
            _returning = true;
            // Snap back to the edge so the NPC doesn't lose the target mid-air
            float clampX = Mathf.Clamp(pos.x, -boundaryLimit, boundaryLimit);
            float clampZ = Mathf.Clamp(pos.z, -boundaryLimit, boundaryLimit);
            _rb.MovePosition(new Vector3(clampX, pos.y, clampZ));
        }

        // ── Auto-return: walk toward center ignoring player input ──
        if (_returning)
        {
            Vector3 toCenter = new Vector3(0f, 0f, 0f) - _rb.position;
            toCenter.y = 0f;

            if (toCenter.magnitude < returnThreshold)
            {
                _returning = false;
            }
            else
            {
                Vector3 dir = toCenter.normalized;
                Quaternion target = Quaternion.LookRotation(dir);
                transform.rotation = Quaternion.RotateTowards(
                    transform.rotation, target, rotationSpeed * Time.fixedDeltaTime);
                _rb.MovePosition(_rb.position + dir * returnSpeed * Time.fixedDeltaTime);
            }
            return;
        }

        // ── Normal WASD movement ───────────────────────────────────
        var kb = Keyboard.current;
        if (kb == null) return;

        float h = 0f, v = 0f;
        if (kb.aKey.isPressed || kb.leftArrowKey.isPressed)  h = -1f;
        if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) h =  1f;
        if (kb.sKey.isPressed || kb.downArrowKey.isPressed)  v = -1f;
        if (kb.wKey.isPressed || kb.upArrowKey.isPressed)    v =  1f;

        Vector3 moveDir = new Vector3(h, 0f, v).normalized;

        if (moveDir.magnitude > 0.1f)
        {
            Quaternion lookTarget = Quaternion.LookRotation(moveDir);
            transform.rotation = Quaternion.RotateTowards(
                transform.rotation, lookTarget, rotationSpeed * Time.fixedDeltaTime);
        }

        _rb.MovePosition(_rb.position + moveDir * speed * Time.fixedDeltaTime);
    }
}